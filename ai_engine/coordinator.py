"""Food Analysis Coordinator.

Orchestrates the multi-agent workflow for food analysis.
"""

from typing import Any, Dict, List, Optional

from ai_engine.agents.detection_agent import DetectionAgent
from ai_engine.agents.nutrition_agent import NutritionAgent
from ai_engine.agents.portion_agent import PortionAgent
from ai_engine.config.model_config import ModelConfig


class FoodAnalysisCoordinator:
    """Coordinator for multi-agent food analysis workflow.

    Orchestrates the detection, portion estimation, and nutrition
    calculation pipeline using specialized agents.

    Attributes:
        config: Model configuration settings.
        detection_agent: YOLOv8 food detection agent.
        portion_agent: XGBoost portion estimation agent.
        nutrition_agent: Nutrition lookup agent.
    """

    def __init__(self, config: Optional[ModelConfig] = None) -> None:
        """Initialize the coordinator and all agents.

        Args:
            config: Optional model configuration. Uses defaults if not provided.
        """
        self.config = config or ModelConfig()

        # Initialize agents
        self.detection_agent = DetectionAgent(
            model_path=self.config.yolo_model_path,
            confidence_threshold=self.config.confidence_threshold,
        )
        self.portion_agent = PortionAgent(
            model_path=self.config.portion_model_path,
        )
        self.nutrition_agent = NutritionAgent()

    def analyze_image(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """Run complete food analysis pipeline on an image.

        Args:
            image_path: Path to the food image.

        Returns:
            Analysis results including detections, portions, and nutrition.
        """
        # Step 1: Detect food items
        detections = self.detection_agent.detect(image_path)

        if not detections:
            return {
                "success": True,
                "detections": [],
                "total_nutrition": {
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fats": 0,
                },
                "message": "No food items detected in image.",
            }

        # Step 2: Estimate portions with unit info for each detection
        for detection in detections:
            portion_info = self.portion_agent.estimate_portion_with_unit(
                food_class=detection["class"],
                bbox=detection["bbox"],
                image_path=image_path,
            )
            detection["estimated_grams"] = portion_info["grams"]
            detection["portion_unit"] = portion_info["unit"]
            detection["portion_amount"] = portion_info["amount"]
            detection["portion_display"] = portion_info["display"]

        # Step 2b: Group count-based foods (e.g., 3 roti detections → "3 roti")
        grouped_detections = self._group_count_based(detections)

        # Step 3: Calculate nutrition for each item
        total_calories = 0.0
        total_protein = 0.0
        total_carbs = 0.0
        total_fats = 0.0

        for detection in grouped_detections:
            nutrition = self.nutrition_agent.get_nutrition(
                food_class=detection["class"],
                grams=detection["estimated_grams"],
            )
            detection["nutrition"] = nutrition

            total_calories += nutrition["calories"]
            total_protein += nutrition["protein"]
            total_carbs += nutrition["carbs"]
            total_fats += nutrition["fats"]

        return {
            "success": True,
            "detections": grouped_detections,
            "total_nutrition": {
                "calories": round(total_calories, 1),
                "protein": round(total_protein, 1),
                "carbs": round(total_carbs, 1),
                "fats": round(total_fats, 1),
            },
        }

    def _group_count_based(
        self,
        detections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Group count-based food detections (e.g., roti).

        Multiple roti detections become a single entry with count.
        Gram-based foods are passed through unchanged.

        Args:
            detections: List of detection dictionaries.

        Returns:
            Grouped detection list.
        """
        count_foods: Dict[str, Dict[str, Any]] = {}
        gram_foods: List[Dict[str, Any]] = []

        for det in detections:
            if det.get("portion_unit") == "piece":
                food_class = det["class"]
                if food_class in count_foods:
                    count_foods[food_class]["portion_amount"] += 1
                    count_foods[food_class]["estimated_grams"] += det["estimated_grams"]
                    count_foods[food_class][
                        "portion_display"
                    ] = f"{count_foods[food_class]['portion_amount']} {food_class}"
                    # Keep highest confidence bbox
                    if det["confidence"] > count_foods[food_class]["confidence"]:
                        count_foods[food_class]["bbox"] = det["bbox"]
                        count_foods[food_class]["confidence"] = det["confidence"]
                else:
                    count_foods[food_class] = det.copy()
            else:
                gram_foods.append(det)

        return list(count_foods.values()) + gram_foods

    def get_available_classes(self) -> List[str]:
        """Get list of food classes the system can detect.

        Returns:
            List of food class names.
        """
        return self.detection_agent.get_classes()
