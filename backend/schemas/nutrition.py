"""Nutrition Schemas.

Pydantic models for nutrition data validation.
"""

from pydantic import BaseModel, Field


class NutritionInfo(BaseModel):
    """Nutrition information for a food item or meal.

    Attributes:
        calories: Calories in kcal.
        protein: Protein in grams.
        carbs: Carbohydrates in grams.
        fats: Fats in grams.
    """

    calories: float = Field(..., ge=0, description="Calories in kcal")
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fats: float = Field(..., ge=0, description="Fats in grams")


class DailyStats(BaseModel):
    """Daily nutrition statistics.

    Attributes:
        date: Date in ISO format.
        calories_consumed: Total calories consumed today.
        calories_target: Daily calorie target.
        calories_remaining: Remaining calories for the day.
        protein: Total protein consumed.
        carbs: Total carbohydrates consumed.
        fats: Total fats consumed.
        meal_count: Number of meals logged.
    """

    date: str
    calories_consumed: float
    calories_target: int
    calories_remaining: float
    protein: float
    carbs: float
    fats: float
    meal_count: int


class WeeklyTrend(BaseModel):
    """Weekly calorie trend data point.

    Attributes:
        date: Date in ISO format.
        day_name: Short day name (Mon, Tue, etc.).
        calories: Total calories for the day.
    """

    date: str
    day_name: str
    calories: float
