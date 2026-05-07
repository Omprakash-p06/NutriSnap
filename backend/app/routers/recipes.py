from __future__ import annotations

import json
import os
import httpx
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from loguru import logger

from app.auth import get_current_user

router = APIRouter(prefix="/recipes", tags=["recipes"])

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class RecipeRequest(BaseModel):
    ingredients: List[str]
    cuisine: Optional[str] = "any"

class RecipeNutrition(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float

class Recipe(BaseModel):
    title: str
    difficulty: str
    time: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: RecipeNutrition

class RecipeResponse(BaseModel):
    recipes: List[Recipe]

# ─────────────────────────────────────────────────────────────────────────────
# Prompt Template
# ─────────────────────────────────────────────────────────────────────────────

_RECIPE_SYSTEM_PROMPT = """\
You are an expert Chef and Nutritionist. 
Your task is to suggest recipes that can be prepared using the provided ingredients.

Guidelines:
1. Suggest exactly 3 diverse recipes.
2. If a cuisine is specified (e.g., "Indian"), prioritize authentic dishes, spices, and techniques from that cuisine.
3. Ensure nutritional estimates (calories, protein, carbs, fat) are as accurate as possible for the entire dish.
4. Keep instructions clear and step-by-step.
5. If a key ingredient is missing for a recipe, assume it's a pantry staple (salt, oil, water) or mention it.
6. Return ONLY a valid JSON object matching this schema:
{
  "recipes": [
    {
      "title": "Recipe Name",
      "difficulty": "Easy/Medium/Hard",
      "time": "Prep + Cook time (e.g. 20 mins)",
      "ingredients": ["1 cup ingredient", "2 tbsp something"],
      "instructions": ["Step 1", "Step 2"],
      "nutrition": {
        "calories": 450,
        "protein": 25,
        "carbs": 40,
        "fat": 15
      }
    }
  ]
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=RecipeResponse)
async def generate_recipes(
    request: RecipeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate 3 recipe suggestions based on ingredients."""
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured.")

    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama-3.3-70b-versatile"

    prompt = f"Ingredients: {', '.join(request.ingredients)}\nCuisine: {request.cuisine}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": _RECIPE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=data, headers=headers, timeout=60.0)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from LLM response
            recipe_data = json.loads(content)
            return recipe_data
            
    except httpx.HTTPStatusError as exc:
        logger.error(f"Groq API error: {exc.response.text}")
        raise HTTPException(status_code=502, detail="AI service error.")
    except Exception as exc:
        logger.error(f"Recipe generation failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to generate recipes.")
