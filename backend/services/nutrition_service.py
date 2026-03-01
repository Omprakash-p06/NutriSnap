"""Nutrition Service.

Provides nutrition data lookup and calculation.
"""

import json
import os
from typing import Dict, Optional

from backend.schemas.nutrition import NutritionInfo

# Nutrition data per 100g for our 4 food classes
NUTRITION_DB: Dict[str, Dict[str, float]] = {
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28.2, "fats": 0.3},
    "dal": {"calories": 130, "protein": 7.5, "carbs": 15.0, "fats": 6.0},
    "paneer": {"calories": 265, "protein": 18.3, "carbs": 1.2, "fats": 20.8},
    "roti": {"calories": 297, "protein": 11.0, "carbs": 51.0, "fats": 5.8},
}

# Weight per piece for count-based foods (grams)
WEIGHT_PER_PIECE: Dict[str, float] = {
    "roti": 40.0,
}


class NutritionService:
    """Service for nutrition data lookup and calculation.

    Attributes:
        nutrition_db: Dictionary of nutrition data per 100g.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize nutrition service.

        Args:
            db_path: Optional path to external nutrition JSON file.
        """
        self.nutrition_db = NUTRITION_DB.copy()

        # Load external database if available
        if db_path and os.path.exists(db_path):
            self._load_external_db(db_path)

    def _load_external_db(self, db_path: str) -> None:
        """Load nutrition data from external JSON file.

        Args:
            db_path: Path to nutrition JSON file.
        """
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.nutrition_db.update(data)
        except (json.JSONDecodeError, IOError):
            pass  # Fall back to built-in database

    def get_nutrition_per_100g(self, food_class: str) -> Optional[NutritionInfo]:
        """Get nutrition information per 100g for a food class.

        Args:
            food_class: Food class name (rice, dal, paneer, roti).

        Returns:
            NutritionInfo for 100g, or None if food not found.
        """
        food_class = food_class.lower()
        if food_class not in self.nutrition_db:
            return None

        data = self.nutrition_db[food_class]
        return NutritionInfo(
            calories=data["calories"],
            protein=data["protein"],
            carbs=data["carbs"],
            fats=data["fats"],
        )

    def calculate_nutrition(
        self,
        food_class: str,
        grams: float,
    ) -> NutritionInfo:
        """Calculate nutrition for a specific portion size.

        Args:
            food_class: Food class name.
            grams: Portion size in grams.

        Returns:
            NutritionInfo scaled to the given portion size.
        """
        base_nutrition = self.get_nutrition_per_100g(food_class)

        if not base_nutrition:
            # Return zeros for unknown foods
            return NutritionInfo(
                calories=0.0,
                protein=0.0,
                carbs=0.0,
                fats=0.0,
            )

        # Scale from per-100g to actual portion
        scale = grams / 100.0

        return NutritionInfo(
            calories=round(base_nutrition.calories * scale, 1),
            protein=round(base_nutrition.protein * scale, 1),
            carbs=round(base_nutrition.carbs * scale, 1),
            fats=round(base_nutrition.fats * scale, 1),
        )

    def get_available_foods(self) -> list:
        """Get list of available food classes.

        Returns:
            List of food class names.
        """
        return list(self.nutrition_db.keys())
