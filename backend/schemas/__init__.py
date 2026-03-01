"""Backend Schemas Package.

Pydantic models for request/response validation.
"""

from backend.schemas.food import AnalysisResponse, DetectedFood
from backend.schemas.meal import MealCreate, MealResponse, MealUpdate
from backend.schemas.nutrition import DailyStats, NutritionInfo, WeeklyTrend

__all__ = [
    "AnalysisResponse",
    "DetectedFood",
    "MealCreate",
    "MealResponse",
    "MealUpdate",
    "NutritionInfo",
    "DailyStats",
    "WeeklyTrend",
]
