"""Tests for IngredientMappingService."""

from pathlib import Path

import pytest
from app.services.mapping import IngredientMappingService

SAMPLE_CSV = Path(__file__).parent / "fixtures" / "sample_ingredients.csv"


@pytest.fixture
def service(tmp_path):
    """Service backed by a tiny in-memory CSV."""
    csv_path = tmp_path / "ingredients.csv"
    csv_path.write_text(
        "food_name,ingredients,primary_category,calories_per_100g,protein_g,carbs_g,fats_g\n"
        'biryani,"basmati rice, chicken",Indian Main Course,190,12,28,5\n'
        'pizza,"dough, cheese, tomato",Fast Food,266,11,33,10\n'
    )
    return IngredientMappingService(csv_path=str(csv_path))


def test_exact_lookup(service):
    result = service.lookup("biryani")
    assert result is not None
    assert "basmati rice" in result["ingredients"]


def test_case_insensitive_lookup(service):
    result = service.lookup("Biryani")
    assert result is not None


def test_fuzzy_lookup(service):
    # "biryani rice" should fuzzy-match "biryani"
    result = service.lookup("biryani rice")
    assert result is not None


def test_missing_returns_none(service):
    result = service.lookup("unicorn meat")
    assert result is None


def test_enrich_items(service):
    items = [
        {"label": "biryani", "calories": 190.0},
        {"label": "pizza", "calories": 266.0},
    ]
    enriched = service.enrich(items)
    assert all("ingredients" in i for i in enriched)
    assert "basmati rice" in enriched[0]["ingredients"]


def test_enrich_unknown_item(service):
    items = [{"label": "mystery_food", "calories": 100.0}]
    enriched = service.enrich(items)
    assert enriched[0]["ingredients"] == ""
    assert enriched[0]["primary_category"] == "Unknown"
