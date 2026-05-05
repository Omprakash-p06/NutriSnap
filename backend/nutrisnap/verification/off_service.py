"""OpenFoodFacts client for nutritional lookup."""

import openfoodfacts
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

class OpenFoodFactsService:
    """Client for OpenFoodFacts API."""

    def __init__(self):
        self.api = openfoodfacts.API(user_agent="NutriSnap/1.0")

    def lookup_food(self, food_name: str) -> dict | None:
        """Search for a food item and return nutrition data per 100g."""
        try:
            results = self.api.product.text_search(food_name)
            if not results or not results.get("products"):
                return None
            
            # Take the first product with nutrition data
            for product in results["products"]:
                nutriments = product.get("nutriments")
                if not nutriments:
                    continue
                
                return {
                    "label": product.get("product_name", food_name),
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "fat": nutriments.get("fat_100g", 0),
                    "score": product.get("nutriscore_grade", "unknown"),
                    "source": "openfoodfacts"
                }
        except Exception as e:
            logger.error(f"OpenFoodFacts search failed for '{food_name}': {e}")
            
        return None
