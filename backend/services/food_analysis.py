"""Food Analysis Service.

Wraps the physical AI engine Coordinator to serve standard API schemas.
"""

from typing import Dict, Any

from backend.schemas.food import AnalysisResponse, DetectedFood
from backend.schemas.nutrition import NutritionInfo
from ai_engine.coordinator import FoodAnalysisCoordinator


class FoodAnalysisService:
    """Service wrapping food analysis functionality."""

    def __init__(self) -> None:
        """Initialize the AI coordinator."""
        self.coordinator = FoodAnalysisCoordinator()

    def analyze_image(self, image_path: str, image_id: str) -> AnalysisResponse:
        """Run image analysis and transform result into API schemas.
        
        Args:
            image_path: Path to the image file.
            image_id: Unique identifier for the image.
            
        Returns:
            AnalysisResponse with detected foods and nutrition values.
        """
        # Run AI pipeline
        raw_result = self.coordinator.analyze_image(image_path)
        
        # Transform detections
        detected_foods = []
        for det in raw_result.get("detections", []):
            detected_foods.append(
                DetectedFood(
                    food_class=det["class"],
                    confidence=det["confidence"],
                    bbox=det["bbox"],
                    estimated_grams=det["estimated_grams"],
                    portion_unit=det.get("portion_unit", "g"),
                    portion_amount=det.get("portion_amount", det["estimated_grams"]),
                    portion_display=det.get("portion_display", f"{det['estimated_grams']}g"),
                    nutrition=NutritionInfo(**det["nutrition"]) if "nutrition" in det else None,
                )
            )
            
        # Parse total nutrition
        total_nutrition_data = raw_result.get("total_nutrition", {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0
        })
        total_nutrition = NutritionInfo(**total_nutrition_data)
        
        return AnalysisResponse(
            success=raw_result.get("success", False),
            image_id=image_id,
            detected_foods=detected_foods,
            total_nutrition=total_nutrition
        )
