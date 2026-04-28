"""app/utils/mapping.py — MappingService shim.

Re-exports IngredientMappingService from app/services/mapping.py,
satisfying the path expected by 02-03-PLAN.md.
"""

from app.services.mapping import (  # noqa: F401
    IngredientMappingService as MappingService,
)

__all__ = ["MappingService"]
