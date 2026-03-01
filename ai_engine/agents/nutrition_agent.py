"""Nutrition Agent.

Agent for nutrition lookup and calculation.
"""

from typing import Dict

from backend.services.nutrition_service import NutritionService


class NutritionAgent:
    """Agent for nutrition lookup and calculation.

    Wraps the NutritionService for use in the agent pipeline.

    Attributes:
        service: Underlying nutrition service.
    """

    def __init__(self) -> None:
        """Initialize nutrition agent."""
        self.service = NutritionService()

    def get_nutrition(
        self,
        food_class: str,
        grams: float,
    ) -> Dict[str, float]:
        """Get nutrition information for a food portion.

        Args:
            food_class: Food class name (rice, dal, paneer, roti).
            grams: Portion size in grams.

        Returns:
            Dictionary with calories, protein, carbs, fats.
        """
        nutrition = self.service.calculate_nutrition(food_class, grams)

        return {
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "carbs": nutrition.carbs,
            "fats": nutrition.fats,
        }

    def get_nutrition_per_100g(
        self,
        food_class: str,
    ) -> Dict[str, float]:
        """Get nutrition information per 100g.

        Args:
            food_class: Food class name.

        Returns:
            Dictionary with calories, protein, carbs, fats per 100g.
        """
        nutrition = self.service.get_nutrition_per_100g(food_class)

        if nutrition is None:
            return {
                "calories": 0.0,
                "protein": 0.0,
                "carbs": 0.0,
                "fats": 0.0,
            }

        return {
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "carbs": nutrition.carbs,
            "fats": nutrition.fats,
        }

    def get_available_foods(self) -> list:
        """Get list of available food classes.

        Returns:
            List of food class names.
        """
        return self.service.get_available_foods()
