# 02-03 Summary: Ingredient Mapping Service

## Status: COMPLETE ✅

## What Was Built
- **`backend/data/ingredients.csv`**: 50+ foods (Indian, Chinese, Italian, Western) with ingredients, category, and per-100g macros.
- **`backend/app/services/mapping.py`**: `IngredientMappingService` singleton:
  - O(1) dict lookup (case-insensitive).
  - `difflib.get_close_matches` fuzzy fallback (cutoff=0.65).
  - `enrich(items)` method annotates pipeline result items in-place.
- **`backend/app/utils/mapping.py`**: Shim re-exporting as `MappingService`.
- **`backend/app/main.py`**: `IngredientMappingService` initialized at startup (no GPU needed).

## Tests
- `test_mapping_service.py::test_exact_lookup` ✅
- `test_mapping_service.py::test_case_insensitive_lookup` ✅
- `test_mapping_service.py::test_fuzzy_lookup` ✅
- `test_mapping_service.py::test_missing_returns_none` ✅
- `test_mapping_service.py::test_enrich_items` ✅
- `test_mapping_service.py::test_enrich_unknown_item` ✅
