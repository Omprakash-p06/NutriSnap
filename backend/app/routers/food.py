"""Food search endpoint with 3-tier fallback:
1. OpenFoodFacts — free global product DB (great for packaged foods)
2. Gemini AI — generates authoritative nutrition for ANY dish (Indian, regional, etc.)
3. Local JSON DB — ultra-fast fallback for common items
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, Query
from loguru import logger

router = APIRouter(prefix="/food", tags=["food"])

# ── Local DB (Tier 3 fallback) ────────────────────────────────────────────────
_db_path = Path(__file__).parent.parent.parent / "data" / "food_database.json"
try:
    with _db_path.open(encoding="utf-8") as f:
        FOOD_DB: list[dict] = json.load(f)
except FileNotFoundError:
    FOOD_DB = []


def _search_local(q: str) -> dict | None:
    """Search the tiny local JSON DB."""
    q_lower = q.lower()
    results = [item for item in FOOD_DB if q_lower in item["name"].lower()]
    if results:
        food = results[0]
        return {
            "name": food["name"],
            "calories_per_100g": food.get("calories_per_100g", 0),
            "protein_per_100g": food.get("protein_per_100g", 0),
            "carbs_per_100g": food.get("carbs_per_100g", 0),
            "fat_per_100g": food.get("fat_per_100g", 0),
            "source": "local_db",
        }
    return None


# ── Tier 1: OpenFoodFacts ─────────────────────────────────────────────────────


def _search_off(q: str) -> dict | None:
    """Search OpenFoodFacts (free, no key, huge global DB)."""
    try:
        import openfoodfacts  # type: ignore

        api = openfoodfacts.API(user_agent="NutriSnap/1.0")
        results = api.product.text_search(q, page_size=5)
        if not results or not results.get("products"):
            return None

        for product in results["products"]:
            nutriments = product.get("nutriments") or {}
            cal = nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g")
            if not cal:
                continue  # skip products with no calorie data
            name = product.get("product_name") or product.get("product_name_en") or q
            return {
                "name": name.strip().title(),
                "calories_per_100g": round(float(cal), 1),
                "protein_per_100g": round(
                    float(nutriments.get("proteins_100g") or 0), 1
                ),
                "carbs_per_100g": round(
                    float(nutriments.get("carbohydrates_100g") or 0), 1
                ),
                "fat_per_100g": round(float(nutriments.get("fat_100g") or 0), 1),
                "source": "openfoodfacts",
            }
    except Exception as exc:
        logger.debug(f"OpenFoodFacts failed for '{q}': {exc}")
    return None


# ── Tier 2: Gemini AI ─────────────────────────────────────────────────────────


async def _search_gemini(q: str) -> dict | None:
    """Ask Gemini for nutrition of ANY food (handles all regional/Indian dishes)."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    prompt = f"""You are a precise nutrition database. Return ONLY a valid JSON object — no markdown, no explanation.

For the food: "{q}"

Return this exact structure (values per 100g, rounded to 1 decimal):
{{
  "name": "<canonical dish name>",
  "calories_per_100g": <number>,
  "protein_per_100g": <number>,
  "carbs_per_100g": <number>,
  "fat_per_100g": <number>
}}

Rules:
- Use authoritative nutrition values (USDA, NIN India, or equivalent scientific source)
- For composite dishes (e.g. curd rice, dal makhani), use typical home-cooked serving composition
- If the food doesn't exist, return {{"error": "not_found"}}
- Return ONLY the JSON object, nothing else"""

    try:
        import asyncio

        import google.generativeai as genai  # type: ignore

        def _sync_call() -> str:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            resp = model.generate_content(prompt)
            return getattr(resp, "text", "") or ""

        raw = await asyncio.to_thread(_sync_call)

        # Strip markdown code fences if present
        import re

        raw = raw.strip()
        if "```" in raw:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if m:
                raw = m.group(1)
        # Extract first JSON object
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return None
        data = json.loads(m.group())
        if data.get("error") == "not_found":
            return None

        cal = data.get("calories_per_100g")
        if not cal:
            return None

        return {
            "name": str(data.get("name", q)).strip(),
            "calories_per_100g": round(float(cal), 1),
            "protein_per_100g": round(float(data.get("protein_per_100g") or 0), 1),
            "carbs_per_100g": round(float(data.get("carbs_per_100g") or 0), 1),
            "fat_per_100g": round(float(data.get("fat_per_100g") or 0), 1),
            "source": "gemini_ai",
        }
    except Exception as exc:
        logger.warning(f"Gemini food search failed for '{q}': {exc}")
    return None


# ── Route ─────────────────────────────────────────────────────────────────────


@router.get("/search")
async def search_food(
    q: str = Query(..., min_length=2, description="Food name to search"),
):
    """Search for any food with 3-tier fallback.

    Tier 1: OpenFoodFacts (free global DB, great for packaged foods)
    Tier 2: Gemini AI  (handles ALL dishes — Indian, regional, homemade)
    Tier 3: Local JSON DB (30 common items, ultra-fast)
    """
    q = q.strip()
    logger.info(f"Food search: '{q}'")

    # Tier 1 — OpenFoodFacts
    result = _search_local(q)  # try local first (fastest, zero network)
    if result:
        logger.debug(f"Food search '{q}' → local DB hit")
        return [result]

    off_result = _search_off(q)
    if off_result:
        logger.info(f"Food search '{q}' → OpenFoodFacts hit ({off_result['name']})")
        return [off_result]

    # Tier 2 — Gemini AI (catches everything: curd rice, pav bhaji, etc.)
    ai_result = await _search_gemini(q)
    if ai_result:
        logger.info(f"Food search '{q}' → Gemini AI hit ({ai_result['name']})")
        return [ai_result]

    # Nothing found
    logger.warning(f"Food search '{q}' → no results from any source")
    return []


@router.get("/database")
async def list_foods(skip: int = 0, limit: int = 50):
    """Return a paginated list of all foods in the local database."""
    return {"total": len(FOOD_DB), "items": FOOD_DB[skip : skip + limit]}
