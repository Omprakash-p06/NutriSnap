"""Meal Schemas.

Pydantic models for meal CRUD operations.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FoodItemCreate(BaseModel):
    """Food item creation schema.

    Attributes:
        food_class: Food class name.
        confidence: Detection confidence.
        ai_portion_grams: AI estimated portion.
        user_portion_grams: User corrected portion.
        calories: Calories for this item.
        protein: Protein in grams.
        carbs: Carbs in grams.
        fats: Fats in grams.
    """

    food_class: str
    confidence: float = 0.0
    ai_portion_grams: float
    user_portion_grams: Optional[float] = None
    calories: float
    protein: float
    carbs: float
    fats: float


class FoodItemResponse(BaseModel):
    """Food item response schema.

    Attributes:
        id: Food item ID.
        food_class: Food class name.
        confidence: Detection confidence.
        ai_portion_grams: AI estimated portion.
        user_portion_grams: User corrected portion.
        calories: Calories for this item.
        protein: Protein in grams.
        carbs: Carbs in grams.
        fats: Fats in grams.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    food_class: str
    confidence: float
    ai_portion_grams: float
    user_portion_grams: float
    calories: float
    protein: float
    carbs: float
    fats: float


class MealCreate(BaseModel):
    """Meal creation schema.

    Attributes:
        user_id: User ID (optional, defaults to 1).
        image_url: URL or path to meal image.
        total_calories: Total meal calories.
        total_protein: Total protein in grams.
        total_carbs: Total carbs in grams.
        total_fats: Total fats in grams.
        food_items: List of food items in the meal.
    """

    user_id: Optional[int] = None
    image_url: Optional[str] = None
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    food_items: List[FoodItemCreate] = Field(default_factory=list)


class MealUpdate(BaseModel):
    """Meal update schema.

    All fields are optional for partial updates.
    """

    total_calories: Optional[float] = None
    total_protein: Optional[float] = None
    total_carbs: Optional[float] = None
    total_fats: Optional[float] = None


class MealResponse(BaseModel):
    """Meal response schema.

    Attributes:
        id: Meal ID.
        user_id: User ID.
        image_url: URL or path to meal image.
        total_calories: Total meal calories.
        total_protein: Total protein in grams.
        total_carbs: Total carbs in grams.
        total_fats: Total fats in grams.
        logged_at: Timestamp when meal was logged.
        food_items: List of food items in the meal.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_url: Optional[str] = None
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    logged_at: datetime
    food_items: List[FoodItemResponse] = Field(default_factory=list)
