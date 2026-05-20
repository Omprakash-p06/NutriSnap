"""Meal planning and daily summary endpoints."""

import json
import os
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_database
from app.utils.nutrition import (
    calculate_bmr,
    calculate_tdee,
    adjust_for_goal,
    macros_from_calories,
)
from nutrisnap.verification.llm_service import LLMService

router = APIRouter(prefix="/planning", tags=["planning"])


@lru_cache(maxsize=1)
def _meal_llm() -> LLMService:
    preferred_provider = os.getenv("MEAL_LLM_PROVIDER")
    provider = preferred_provider or (
        "openrouter" if os.getenv("OPENROUTER_API_KEY") else "local"
    )
    model_name = os.getenv("MEAL_LLM_MODEL")
    if not model_name:
        if provider == "openrouter":
            model_name = "google/gemma-4-26b-a4b-it:free"
        elif provider == "local":
            model_name = "gemma4:2b"
        else:
            model_name = "google/gemma-4-26b-a4b-it:free"

    llm = LLMService(provider=provider, model_name=model_name)
    llm.provider_order = [provider] + (["local"] if provider == "openrouter" else [])
    return llm


def _dietary_preferences(current_user: dict) -> list[str]:
    settings = current_user.get("settings") or {}
    if isinstance(settings, str):
        try:
            settings = json.loads(settings)
        except Exception:
            settings = {}
    if isinstance(settings, dict):
        return settings.get("dietaryPreferences", []) or []
    return []


class RecipeDetailsRequest(BaseModel):
    name: str
    type: str | None = None
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None


def _fallback_suggestions(remaining: dict[str, float]) -> list[dict]:
    """Return randomized meal suggestions when the LLM is unavailable."""
    import random
    calorie_budget = max(0, remaining["calories"])
    split = [0.28, 0.32, 0.28, 0.12]
    
    meal_pools = {
        "Breakfast": [
            ("High-protein yogurt bowl", "Simple, light breakfast to preserve later calories."),
            ("Oatmeal with fresh berries", "Fiber-rich start to boost morning metabolism."),
            ("Spinach and egg scramble", "Protein-dense breakfast with low carb density."),
            ("Avocado toast with poached egg", "Healthy fats and quality protein to sustain energy.")
        ],
        "Lunch": [
            ("Grilled chicken rice bowl", "Anchors the day with balanced protein and carbs."),
            ("Tofu stir-fry with quinoa", "Plant-based recovery meal with essential amino acids."),
            ("Turkey and spinach wrap", "Lean protein wrap, perfect for an active midday refresh."),
            ("Lentil and vegetable salad", "Nutrient-packed fiber and protein combination.")
        ],
        "Dinner": [
            ("Vegetable dal and roti", "Keeps dinner filling without overshooting calories."),
            ("Baked salmon with broccoli", "Omega-3 rich dinner supporting muscle recovery."),
            ("Lean beef and cauliflower rice", "Low-carb high-protein satisfying dinner."),
            ("Black bean and sweet potato bowl", "Hearty vegetarian dinner with complex carbs.")
        ],
        "Snack": [
            ("Fruit and nuts", "Provides a small satiety boost with minimal prep."),
            ("Greek yogurt with honey", "Quick probiotic protein snack."),
            ("Apple slices with peanut butter", "Balanced healthy fats and fresh fruit fiber."),
            ("Protein shake", "Fast muscle recovery supplement post-exercise.")
        ]
    }

    meal_templates = []
    for mtype in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        name, why = random.choice(meal_pools[mtype])
        meal_templates.append((mtype, name, why))

    suggestions = []
    for idx, ((meal_type, name, why), share) in enumerate(zip(meal_templates, split), start=1):
        calories = round(calorie_budget * share, 0)
        suggestions.append(
            {
                "id": f"fallback-{idx}",
                "name": name,
                "type": meal_type,
                "calories": calories,
                "protein": round(max(8, calories * 0.08), 1),
                "carbs": round(max(12, calories * 0.12), 1),
                "fat": round(max(4, calories * 0.04), 1),
                "why": why,
                "image_url": f"https://image.pollinations.ai/prompt/{urllib.parse.quote(name)}?width=500&height=350&nologo=true",
            }
        )

    return suggestions


@router.get("/daily-summary")
async def daily_summary(current_user: dict = Depends(get_current_user)):
    """Aggregate today's logged meals into calorie and macro totals."""
    db = await get_database()
    user_email = current_user["email"]
    
    # Start of today in UTC
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).strftime("%Y-%m-%d %H:%M:%S")

    query = "SELECT * FROM meal_logs WHERE user_email = ? AND timestamp >= ?"
    async with db.execute(query, (user_email, today_start)) as cursor:
        rows = await cursor.fetchall()
        logs = [dict(r) for r in rows]

    return {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "calories": round(sum(log.get("calories", 0) for log in logs), 1),
        "protein": round(sum(log.get("protein", 0) for log in logs), 1),
        "carbs": round(sum(log.get("carbs", 0) for log in logs), 1),
        "fat": round(sum(log.get("fat", 0) for log in logs), 1),
        "meals_logged": len(logs),
    }


@router.get("/weekly-summary")
async def weekly_summary(current_user: dict = Depends(get_current_user)):
    """Return daily calorie totals for the last 7 days."""
    db = await get_database()
    user_email = current_user["email"]
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = []
    
    for i in range(7):
        day_start = (today - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
        day_end = (today - timedelta(days=i-1)).strftime("%Y-%m-%d %H:%M:%S")
        
        query = "SELECT SUM(calories) as total FROM meal_logs WHERE user_email = ? AND timestamp >= ? AND timestamp < ?"
        async with db.execute(query, (user_email, day_start, day_end)) as cursor:
            row = await cursor.fetchone()
            total_cal = row["total"] if row and row["total"] else 0
            
        result.append({
            "date": (today - timedelta(days=i)).date().isoformat(),
            "calories": round(total_cal, 1),
        })
        
    return list(reversed(result))


@router.post("/suggest")
async def suggest_meals(current_user: dict = Depends(get_current_user)):
    """Generate 4 AI meal suggestions based on user profile and remaining macros."""
    # 1. Get targets
    required = ["weight_kg", "height_cm", "age", "gender", "activity_level", "goal"]
    missing = [f for f in required if not current_user.get(f)]
    
    if missing:
        # Fallback to defaults if profile is incomplete
        targets = {
            "target_calories": 2000,
            "protein_g": 150,
            "carbs_g": 200,
            "fat_g": 70
        }
    else:
        bmr = calculate_bmr(
            current_user["weight_kg"],
            current_user["height_cm"],
            current_user["age"],
            current_user["gender"],
        )
        tdee = calculate_tdee(bmr, current_user["activity_level"])
        target_calories = adjust_for_goal(tdee, current_user["goal"])
        macros = macros_from_calories(target_calories)
        targets = {
            "target_calories": target_calories,
            "protein_g": macros["protein_g"],
            "carbs_g": macros["carbs_g"],
            "fat_g": macros["fat_g"]
        }

    # 2. Get today's intake
    summary = await daily_summary(current_user)
    
    remaining = {
        "calories": max(0, targets["target_calories"] - summary["calories"]),
        "protein": max(0, targets["protein_g"] - summary["protein"]),
        "carbs": max(0, targets["carbs_g"] - summary["carbs"]),
        "fat": max(0, targets["fat_g"] - summary["fat"]),
    }

    try:
        import random
        cuisines = [
            "Indian", "Mediterranean", "Mexican", "Japanese", "Italian", "American", "Middle Eastern",
            "Thai", "Vietnamese", "Korean", "Greek", "Spanish", "French", "Caribbean", "Nordic",
            "Asian Fusion", "Tex-Mex", "South American", "African", "Eastern European"
        ]
        random_cuisine = random.choice(cuisines)
        
        ingredients_focus = [
            "chicken", "salmon", "tofu", "lentils", "quinoa", "eggs", "avocado", "spinach", "sweet potatoes",
            "chickpeas", "Greek yogurt", "berries", "oats", "turkey", "beef", "black beans", "broccoli",
            "mushrooms", "bell peppers", "shrimp", "chia seeds"
        ]
        random_ingredient1 = random.choice(ingredients_focus)
        random_ingredient2 = random.choice([i for i in ingredients_focus if i != random_ingredient1])

        dietary_preferences = _dietary_preferences(current_user)
        prompt = f"""
        Suggest 4 distinct healthy meals for today (Breakfast, Lunch, Dinner, and a Snack/Light Meal).

        To ensure variety, focus on:
        - Cuisine Theme: {random_cuisine}
        - Featured Ingredients to incorporate: {random_ingredient1}, {random_ingredient2}
        """

        prompt += f"""
        User Profile:
        - Name: {current_user.get('full_name', 'User')}
        - Location: {current_user.get('location', 'unknown')}
        - Goal: {current_user.get('goal', 'maintenance')}
        - Age: {current_user.get('age', 'unknown')}
        - Gender: {current_user.get('gender', 'unknown')}
        - Activity Level: {current_user.get('activity_level', 'unknown')}
        - Weight: {current_user.get('weight_kg', 'unknown')}kg, Height: {current_user.get('height_cm', 'unknown')}cm
        - Dietary Preferences: {', '.join(dietary_preferences) if dietary_preferences else 'none'}

        Remaining budget for today:
        - Calories: {remaining['calories']:.0f} kcal
        - Protein: {remaining['protein']:.0f} g
        - Carbs: {remaining['carbs']:.0f} g
        - Fat: {remaining['fat']:.0f} g

        Your task is to generate 4 meal suggestions that fit within this budget.
        For each meal, provide:
        - name: A short, appealing name.
        - type: One of "Breakfast", "Lunch", "Dinner", "Snack".
        - calories: Estimated calories (number).
        - protein: Estimated protein in grams (number).
        - carbs: Estimated carbohydrates in grams (number).
        - fat: Estimated fat in grams (number).
        - why: A brief (1-sentence) justification for why this meal is a good choice for the user's goals and remaining budget.
        - image_url: An image URL from Pollinations AI (e.g., https://image.pollinations.ai/prompt/healthy%20meal%20name). URL encode the meal name for the prompt.

        IMPORTANT: Respond with ONLY a valid, parseable JSON array of 4 meal objects, like this:
        [
            {{"name": "...", "type": "Breakfast", ...}},
            {{"name": "...", "type": "Lunch", ...}},
            ...
        ]
        Do not include any other text, greetings, or explanations outside the JSON.
        """
        llm = _meal_llm()
        response_text = await llm.generate_text(prompt)
        
        if not response_text:
            raise ValueError("LLM returned an empty response.")

        suggestions = json.loads(response_text)
        
        # Add IDs if missing and override image_url programmatically to match the suggested meal name
        for i, s in enumerate(suggestions):
            if "id" not in s:
                s["id"] = f"llm-{i}-{int(time.time())}"
            meal_name = s.get("name", "healthy meal")
            s["image_url"] = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(meal_name)}?width=500&height=350&nologo=true"

        return suggestions

    except Exception as e:
        logger.error(f"Meal suggestion failed: {e}")
        return _fallback_suggestions(remaining)


@router.get("/recipe-details/{meal_id}")
async def get_recipe_details(meal_id: str, current_user: dict = Depends(get_current_user)):
    """Provides mock recipe details for a given meal ID."""
    # In a real app, you'd look this up in a database or use another LLM call.
    # For this fix, we'll return a plausible-looking mock response.
    logger.info(f"Fetching mock recipe details for meal_id: {meal_id} for user {current_user['email']}")
    
    # Simple deterministic mock based on meal_id
    if "fallback" in meal_id:
        ingredients = ["Greek Yogurt (1 cup)", "Berries (1/2 cup)", "Granola (1/4 cup)", "Honey (1 tbsp)"]
        instructions = "Combine all ingredients in a bowl. Enjoy your simple and protein-packed breakfast!"
    elif "llm" in meal_id:
        ingredients = ["Chicken Breast (150g)", "Brown Rice (1 cup, cooked)", "Broccoli (1 cup)", "Soy Sauce (2 tbsp)", "Garlic (1 clove)"]
        instructions = "1. Grill chicken until cooked through. 2. Steam broccoli. 3. Combine all ingredients in a bowl and drizzle with soy sauce."
    else:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return {
        "meal_id": meal_id,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition": { # Placeholder nutrition
            "calories": 450,
            "protein": 40,
            "carbs": 45,
            "fat": 10
        }
    }
