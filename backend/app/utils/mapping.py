"""app/utils/mapping.py — MappingService shim.

Re-exports IngredientMappingService from app/services/mapping.py,
satisfying the path expected by 02-03-PLAN.md.
"""
from app.services.mapping import IngredientMappingService as MappingService  # noqa: F401

__all__ = ["MappingService"]
