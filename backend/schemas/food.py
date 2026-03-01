"""Food Detection Schemas.

Pydantic models for food analysis request/response.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from backend.schemas.nutrition import NutritionInfo


class DetectedFood(BaseModel):
    """Detected food item with bounding box and nutrition.

    Attributes:
        food_class: Food class name (rice, dal, paneer, roti).
        confidence: Detection confidence score (0-1).
        bbox: Bounding box coordinates [x1, y1, x2, y2].
        estimated_grams: AI estimated portion in grams.
        nutrition: Nutrition information for this item.
    """

    food_class: str = Field(..., description="Food class name")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    bbox: List[int] = Field(
        ..., min_length=4, max_length=4, description="Bounding box [x1, y1, x2, y2]"
    )
    estimated_grams: float = Field(..., ge=0, description="Estimated portion in grams")
    portion_unit: str = Field("g", description="Portion unit (g, piece, etc)")
    portion_amount: float = Field(..., description="Portion amount in given unit")
    portion_display: str = Field(..., description="Formatted string for display")
    nutrition: Optional[NutritionInfo] = None


class AnalysisResponse(BaseModel):
    """Food analysis response.

    Attributes:
        success: Whether analysis was successful.
        image_id: Unique image identifier.
        detected_foods: List of detected food items.
        total_nutrition: Aggregated nutrition for the meal.
    """

    success: bool
    image_id: str
    detected_foods: List[DetectedFood]
    total_nutrition: NutritionInfo
