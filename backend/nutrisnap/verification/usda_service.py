"""USDA Food Data Central API client for Tier 3 verification."""

import os
import httpx
import diskcache
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class USDAService:
    """Client for USDA FoodData Central API with caching."""

    def __init__(self, api_key: str | None = None, cache_dir: str = ".cache/usda"):
        self.api_key = api_key or os.environ.get("USDA_API_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(cache_dir)

    @property
    def is_available(self) -> bool:
        return self.api_key is not None

    async def search_calories(self, food_name: str) -> float | None:
        """Search for a food item and return calories per 100g/ml."""
        if not self.is_available:
            return None

        if food_name in self.cache:
            logger.debug(f"Cache hit for USDA: {food_name}")
            return self.cache[food_name]

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/foods/search"
                params = {
                    "api_key": self.api_key,
                    "query": food_name,
                    "pageSize": 1,
                    "dataType": ["Survey (FNDDS)", "Foundation"],
                }
                res = await client.get(url, params=params)
                res.raise_for_status()
                data = res.json()

                if not data.get("foods"):
                    return None

                food = data["foods"][0]
                # Nutrient ID 208 is Energy (kcal) in FDC
                calories = None
                for nutrient in food.get("foodNutrients", []):
                    if nutrient.get("nutrientId") == 208 or "Energy" in nutrient.get(
                        "nutrientName", ""
                    ):
                        calories = float(nutrient.get("value", 0))
                        break
                
                if calories is not None:
                    self.cache.set(food_name, calories, expire=86400 * 7)
                return calories

        except Exception as e:
            logger.error(f"USDA search failed for '{food_name}': {e}")

        return None
