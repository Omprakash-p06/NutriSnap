"""Food density and nutrition database loader."""

import json
from pathlib import Path
from typing import Optional

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# Default path to density database
DEFAULT_DBPATH = Path(__file__).parent / "densities.json"

# In-memory cache
_density_db: Optional[dict] = None


def load_density_db(db_path: Optional[Path | str] = None) -> dict:
    """Load the food density database.

    Args:
        db_path: Path to densities.json. If None, uses default.

    Returns:
        Dictionary with food density and nutrition data.
    """
    global _density_db

    if _density_db is not None:
        return _density_db

    path = Path(db_path) if db_path else DEFAULT_DBPATH

    if not path.exists():
        logger.warning(f"Density database not found: {path}, using empty database")
        return {"foods": {}, "_fallback": {}, "_metadata": {}}

    with open(path) as f:
        _density_db = json.load(f)

    logger.info(
        f"Loaded density database with {len(_density_db.get('foods', {}))} foods"
    )
    return _density_db


def get_food_density(
    label: str, db: Optional[dict] = None, fuzzy_match: bool = True
) -> Optional[dict]:
    """Get density and nutrition data for a food label.

    Args:
        label: Food name/label (e.g., "chicken", "broccoli").
        db: Optional pre-loaded database. If None, loads default.
        fuzzy_match: If True, try category fallback for unknown foods.

    Returns:
        Dictionary with density (g/cm³) and nutrition per 100g, or None if not found.
    """
    if db is None:
        db = load_density_db()

    # Normalize label
    normalized = label.lower().strip()

    # Direct lookup
    if normalized in db.get("foods", {}):
        return db["foods"][normalized]

    # Try with underscores/spaces normalized
    normalized_alt = normalized.replace(" ", "_")
    if normalized_alt in db.get("foods", {}):
        return db["foods"][normalized_alt]

    # Try fuzzy matching on known foods
    if fuzzy_match:
        foods = db.get("foods", {})

        # Partial match
        for food_key in foods:
            if normalized in food_key or food_key in normalized:
                logger.debug(f"Fuzzy matched '{label}' -> '{food_key}'")
                return foods[food_key]

        # Category fallback
        category_mapping = db.get("_category_mapping", {})
        for category, food_list in category_mapping.items():
            if normalized in food_list:
                # Return first food in category as proxy
                # This is a rough fallback - ideally use LLM for better matching
                logger.debug(
                    f"Category fallback for '{label}' -> using generic {category}"
                )
                return _get_category_proxy(db, category)

    # Return fallback values
    fallback = db.get(
        "_fallback",
        {
            "density": 1.0,
            "calories": 100,
            "protein": 3.0,
            "carbohydrates": 15.0,
            "fat": 3.0,
            "fiber": 2.0,
        },
    )

    logger.debug(f"Using fallback values for unknown food: '{label}'")
    return fallback


def _get_category_proxy(db: dict, category: str) -> dict:
    """Get a generic nutrition profile for a food category.

    This is a rough approximation for when exact matching fails.
    Uses average values from category foods.
    """
    foods = db.get("foods", {})
    category_foods = [f for f in foods.values() if f.get("category") == category]

    if not category_foods:
        return db.get("_fallback", {})

    # Average values from category
    n = len(category_foods)
    return {
        "density": sum(f["density"] for f in category_foods) / n,
        "calories": sum(f["calories"] for f in category_foods) / n,
        "protein": sum(f["protein"] for f in category_foods) / n,
        "carbohydrates": sum(f["carbohydrates"] for f in category_foods) / n,
        "fat": sum(f["fat"] for f in category_foods) / n,
        "fiber": sum(f["fiber"] for f in category_foods) / n,
        "category": category,
    }


def get_nutrition_per_100g(label: str, db: Optional[dict] = None) -> dict:
    """Get nutrition data per 100g for a food label.

    Convenience wrapper around get_food_density.
    """
    return get_food_density(label, db)


def reload_db(db_path: Optional[Path | str] = None) -> dict:
    """Force reload the density database.

    Use when the database file has been updated.
    """
    global _density_db
    _density_db = None
    return load_density_db(db_path)
