"""OpenFoodFacts client for nutritional lookup."""

import os

import diskcache
import openfoodfacts

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class OpenFoodFactsService:
    """Client for OpenFoodFacts API with caching."""

    def __init__(self, cache_dir: str = ".cache/off"):
        self.api = openfoodfacts.API(user_agent="NutriSnap/1.0")
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(cache_dir)

    def lookup_food(self, food_name: str) -> dict | None:
        """Search for a food item and return nutrition data per 100g."""
        if food_name in self.cache:
            logger.debug(f"Cache hit for OpenFoodFacts: {food_name}")
            return self.cache[food_name]

        try:
            results = self.api.product.text_search(food_name)
            if not results or not results.get("products"):
                return None

            # Take the first product with nutrition data
            for product in results["products"]:
                nutriments = product.get("nutriments")
                if not nutriments:
                    continue

                data = {
                    "label": product.get("product_name", food_name),
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "fat": nutriments.get("fat_100g", 0),
                    "saturated_fat": nutriments.get("saturated-fat_100g", 0),
                    "sugars": nutriments.get("sugars_100g", 0),
                    "fiber": nutriments.get("fiber_100g", 0),
                    "score": product.get("nutriscore_grade", "unknown"),
                    "source": "openfoodfacts",
                }
                self.cache.set(food_name, data, expire=86400 * 7)  # 1 week cache
                return data
        except Exception as e:
            logger.error(f"OpenFoodFacts search failed for '{food_name}': {e}")

        return None
