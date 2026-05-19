"""Meal planning and daily summary endpoints."""

import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from loguru import logger

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


def _fallback_suggestions(remaining: dict[str, float]) -> list[dict]:
    """Return deterministic meal suggestions when the LLM is unavailable."""
    calorie_budget = max(0, remaining["calories"])
    split = [0.28, 0.32, 0.28, 0.12]
    meal_templates = [
        ("Breakfast", "High-protein yogurt bowl", "Simple, light breakfast to preserve later calories."),
        ("Lunch", "Grilled chicken rice bowl", "Anchors the day with balanced protein and carbs."),
        ("Dinner", "Vegetable dal and roti", "Keeps dinner filling without overshooting calories."),
        ("Snack", "Fruit and nuts", "Provides a small satiety boost with minimal prep."),
    ]

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
        prompt = f"""
        Suggest 4 distinct healthy meals for today (Breakfast, Lunch, Dinner, and a Snack/Light Meal).

        User Profile:
        - Name: {current_user.get('full_name', 'User')}
        - Location: {current_user.get('location', 'unknown')}
        - Goal: {current_user.get('goal', 'maintenance')}
        - Age: {current_user.get('age', 'unknown')}
        - Gender: {current_user.get('gender', 'unknown')}
        - Activity Level: {current_user.get('activity_level', 'unknown')}
        - Weight: {current_user.get('weight_kg', 'unknown')}kg, Height: {current_user.get('height_cm', 'unknown')}cm
        - Remaining Budget for today: {remaining['calories']:.0f} kcal
        - Remaining Macros: {remaining['protein']:.0f}g Protein, {remaining['carbs']:.0f}g Carbs, {remaining['fat']:.0f}g Fat

        Requirements:
        1. Provide EXACTLY 4 suggestions.
        2. Focus on wholesome, real food ingredients.
        3. Include an estimate of calories and macros for each meal.
        4. Return ONLY a JSON list of objects with these fields:
           - id (string, unique)
           - name (string)
           - type (string: Breakfast, Lunch, Dinner, Snack)
           - calories (number)
           - protein (number)
           - carbs (number)
           - fat (number)
           - why (string: short 1-sentence reason why this fits their profile and goal)
        """
        llm = LLMService(provider=os.getenv("LLM_PROVIDER", "gemini"))
        if llm.is_available:
            suggestions = await llm.generate_json(prompt)
            if isinstance(suggestions, list):
                return suggestions
            if isinstance(suggestions, dict) and "suggestions" in suggestions:
                return suggestions["suggestions"]

        logger.warning("LLM unavailable or returned unexpected format; using deterministic fallback suggestions")
        return _fallback_suggestions(remaining)
        
    except Exception as exc:
        logger.error(f"Failed to generate meal suggestions: {exc}")
        return _fallback_suggestions(remaining)
