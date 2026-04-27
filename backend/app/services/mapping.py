"""IngredientMappingService: O(1) ingredient + nutrition lookup.

Loads a CSV database at startup into memory. Supports fuzzy matching so
"biryani rice" correctly resolves to "biryani".
"""

from __future__ import annotations

import csv
from difflib import get_close_matches
from pathlib import Path
from typing import Optional

from loguru import logger

# Default CSV path relative to the backend root
_DEFAULT_CSV = Path(__file__).parent.parent.parent / "data" / "ingredients.csv"


class IngredientMappingService:
    """Singleton-safe ingredient mapper.

    Attributes:
        _db: Dict mapping lowercase food name → row dict.
    """

    def __init__(self, csv_path: str | Path = _DEFAULT_CSV) -> None:
        self._db: dict[str, dict] = {}
        self._load(Path(csv_path))

    def _load(self, path: Path) -> None:
        if not path.exists():
            logger.warning(f"Ingredient CSV not found at {path}. Mapping will be empty.")
            return
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("food_name", "").strip().lower()
                if name:
                    self._db[name] = row
        logger.info(f"IngredientMappingService loaded {len(self._db)} entries from {path.name}")

    # ── Lookup ──────────────────────────────────────────────────────────────

    def lookup(self, food_name: str) -> Optional[dict]:
        """Exact-then-fuzzy lookup.

        Args:
            food_name: Food label from the ML pipeline (e.g. "Biryani").

        Returns:
            Row dict with ingredient & nutrition info, or None if not found.
        """
        key = food_name.strip().lower()

        # 1. Exact match
        if key in self._db:
            return self._db[key]

        # 2. Fuzzy match (cutoff=0.65 works well for food names)
        candidates = get_close_matches(key, self._db.keys(), n=1, cutoff=0.65)
        if candidates:
            matched = candidates[0]
            logger.debug(f"Fuzzy match: '{food_name}' → '{matched}'")
            return self._db[matched]

        logger.debug(f"No mapping found for '{food_name}'")
        return None

    def enrich(self, items: list[dict]) -> list[dict]:
        """Attach ingredient breakdown to a list of pipeline result items.

        Args:
            items: List of dicts with at least a "label" key.

        Returns:
            Same list with an "ingredients" key added where available.
        """
        for item in items:
            row = self.lookup(item.get("label", ""))
            if row:
                item["ingredients"] = row.get("ingredients", "")
                item["primary_category"] = row.get("primary_category", "")
            else:
                item["ingredients"] = ""
                item["primary_category"] = "Unknown"
        return items
