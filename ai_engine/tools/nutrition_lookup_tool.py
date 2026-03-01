"""Nutrition Lookup Tool.

CrewAI tool for nutrition database lookup.
"""

from typing import Any, Dict, List

from backend.services.nutrition_service import NutritionService


class NutritionLookupTool:
    """Tool for nutrition database lookup.

    Provides nutrition lookup capabilities for CrewAI agents.

    Attributes:
        service: Underlying nutrition service.
    """

    name: str = "nutrition_lookup"
    description: str = "Looks up nutrition information for food items"

    def __init__(self) -> None:
        """Initialize nutrition lookup tool."""
        self.service = NutritionService()

    def lookup(
        self,
        food_class: str,
        grams: float,
    ) -> Dict[str, float]:
        """Look up nutrition for a food portion.

        Args:
            food_class: Food class name.
            grams: Portion size in grams.

        Returns:
            Dictionary with nutrition values.
        """
        nutrition = self.service.calculate_nutrition(food_class, grams)
        return {
            "calories": nutrition.calories,
            "protein": nutrition.protein,
            "carbs": nutrition.carbs,
            "fats": nutrition.fats,
        }

    def get_available_foods(self) -> List[str]:
        """Get list of available food classes.

        Returns:
            List of food class names.
        """
        return self.service.get_available_foods()

    def run(
        self,
        food_class: str,
        grams: float = 100.0,
    ) -> Dict[str, Any]:
        """Run nutrition lookup.

        Args:
            food_class: Food class name.
            grams: Portion size in grams.

        Returns:
            Dictionary with nutrition info and metadata.
        """
        nutrition = self.lookup(food_class, grams)

        return {
            "food_class": food_class,
            "grams": grams,
            "nutrition": nutrition,
            "available_foods": self.get_available_foods(),
        }
