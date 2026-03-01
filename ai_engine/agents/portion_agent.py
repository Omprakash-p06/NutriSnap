"""Portion Estimation Agent.

XGBoost-based portion size estimation agent.
"""

import os
from typing import Any, Dict, List, Optional

import numpy as np


class PortionAgent:
    """Agent for portion size estimation using XGBoost.

    Estimates food weight in grams based on bounding box features.
    Roti uses count-based estimation (1 roti ≈ 40g).
    Rice, dal, paneer use gram-based estimation via XGBoost.

    Attributes:
        model_path: Path to XGBoost model file.
        model: Loaded XGBoost model (lazy loaded).
    """

    # Weight per piece for count-based foods
    ROTI_WEIGHT_PER_PIECE: float = 40.0  # grams

    # Class ID map matching YOLO data.yaml order
    CLASS_ID_MAP: Dict[str, int] = {
        "dal": 0,
        "paneer": 1,
        "rice": 2,
        "roti": 3,
    }

    # Foods that are counted by pieces, not grams
    COUNT_BASED_FOODS: Dict[str, float] = {
        "roti": 40.0,  # grams per piece
    }

    # Default portion sizes per class (S/M/L in grams)
    DEFAULT_PORTIONS: Dict[str, Dict[str, float]] = {
        "rice": {"small": 100.0, "medium": 150.0, "large": 200.0},
        "dal": {"small": 150.0, "medium": 200.0, "large": 250.0},
        "paneer": {"small": 50.0, "medium": 80.0, "large": 120.0},
        "roti": {"small": 30.0, "medium": 40.0, "large": 50.0},
    }

    def __init__(self, model_path: Optional[str] = None) -> None:
        """Initialize portion estimation agent.

        Args:
            model_path: Path to XGBoost model file.
        """
        self.model_path = model_path or "./ml/weights/portion_model.joblib"
        self._model = None
        self._depth_model = None

    @property
    def model(self) -> Any:
        """Lazy load XGBoost model.

        Returns:
            Loaded XGBoost model or None.
        """
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the XGBoost model from file."""
        if not os.path.exists(self.model_path):
            self._model = None
            return

        try:
            import joblib  # pylint: disable=import-outside-toplevel

            self._model = joblib.load(self.model_path)
        except (ImportError, Exception):  # pylint: disable=broad-exception-caught
            self._model = None

    @property
    def depth_model(self) -> Any:
        """Lazy load depth estimation model."""
        if self._depth_model is None:
            try:
                from ai_engine.models.depth_model import DepthModel  # pylint: disable=import-outside-toplevel

                self._depth_model = DepthModel()
            except (ImportError, Exception):  # pylint: disable=broad-exception-caught
                self._depth_model = None
        return self._depth_model

    def extract_depth_features(
        self,
        depth_map: Optional[np.ndarray],
        bbox: List[int],
    ) -> tuple:
        """Extract depth features from a depth map region.

        Args:
            depth_map: Full depth map array, or None.
            bbox: Bounding box [x1, y1, x2, y2].

        Returns:
            Tuple of (mean_depth, max_depth, depth_std).
        """
        if depth_map is None:
            return (0.4, 0.5, 0.05)  # Neutral defaults

        x1, y1, x2, y2 = [int(c) for c in bbox]
        region = depth_map[y1:y2, x1:x2]

        if not region.size:
            return (0.4, 0.5, 0.05)

        # Normalize depth to 0-1 range
        depth_norm = region.astype(float)
        if depth_norm.max() > 1.0:
            depth_norm = depth_norm / 255.0

        return (
            float(np.mean(depth_norm)),
            float(np.max(depth_norm)),
            float(np.std(depth_norm)),
        )

    def extract_features(  # pylint: disable=too-many-locals
        self,
        bbox: List[int],
        class_id: int = 0,
        depth_map: Optional[np.ndarray] = None,
        image_size: tuple = (640, 640),
    ) -> np.ndarray:
        """Extract features from bounding box for portion estimation.

        Args:
            bbox: Bounding box coordinates [x1, y1, x2, y2].
            class_id: YOLO class ID for the food item.
            depth_map: Optional depth map for depth features.
            image_size: Original image size (width, height).

        Returns:
            Feature array for model input (11 features).
        """
        x1, y1, x2, y2 = bbox

        # Box dimensions
        width = x2 - x1
        height = y2 - y1
        area = width * height
        aspect_ratio = width / max(height, 1)

        # Relative to image size
        image_area = image_size[0] * image_size[1]
        relative_area = area / image_area

        # Center position (normalized)
        center_x = ((x1 + x2) / 2) / image_size[0]
        center_y = ((y1 + y2) / 2) / image_size[1]

        # Depth features
        mean_depth, max_depth, depth_std = self.extract_depth_features(depth_map, bbox)

        return np.array(
            [
                area,
                aspect_ratio,
                relative_area,
                width,
                height,
                center_x,
                center_y,
                class_id,
                mean_depth,
                max_depth,
                depth_std,
            ]
        )

    def estimate_portion(
        self,
        food_class: str,
        bbox: List[int],
        image_path: Optional[str] = None,
    ) -> float:
        """Estimate portion size in grams.

        Args:
            food_class: Food class name.
            bbox: Bounding box coordinates [x1, y1, x2, y2].
            image_path: Optional path to image for depth features.

        Returns:
            Estimated portion size in grams.
        """
        food_class_lower = food_class.lower()

        # Count-based foods (roti): each detection = 1 piece
        if food_class_lower in self.COUNT_BASED_FOODS:
            return self.COUNT_BASED_FOODS[food_class_lower]

        # Generate depth map if image is available
        depth_map = None
        if image_path and self.depth_model is not None:
            try:
                import cv2  # pylint: disable=import-outside-toplevel

                image = cv2.imread(image_path)  # pylint: disable=no-member
                if image is not None:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
                    depth_map = self.depth_model.predict(image_rgb)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        # Gram-based foods: use XGBoost model
        class_id = self.CLASS_ID_MAP.get(food_class_lower, 0)
        features = self.extract_features(bbox, class_id=class_id, depth_map=depth_map)

        if self.model is not None:
            try:
                prediction = self.model.predict(features.reshape(1, -1))
                return max(10.0, float(prediction[0]))  # Minimum 10g
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        # Fall back to heuristic-based estimation
        return self._heuristic_estimation(food_class, bbox)

    def estimate_portion_with_unit(
        self,
        food_class: str,
        bbox: List[int],
        image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Estimate portion with unit information.

        Args:
            food_class: Food class name.
            bbox: Bounding box coordinates [x1, y1, x2, y2].
            image_path: Optional path to image.

        Returns:
            Dictionary with amount, unit, and grams.
        """
        food_class_lower = food_class.lower()
        grams = self.estimate_portion(food_class, bbox, image_path)

        if food_class_lower in self.COUNT_BASED_FOODS:
            return {
                "amount": 1,
                "unit": "piece",
                "grams": grams,
                "display": f"1 {food_class_lower}",
            }

        return {
            "amount": round(grams, 1),
            "unit": "g",
            "grams": grams,
            "display": f"{round(grams)}g",
        }

    def _heuristic_estimation(
        self,
        food_class: str,
        bbox: List[int],
    ) -> float:
        """Estimate portion using heuristics when model unavailable.

        Args:
            food_class: Food class name.
            bbox: Bounding box coordinates.

        Returns:
            Estimated portion size in grams.
        """
        food_class = food_class.lower()
        portions = self.DEFAULT_PORTIONS.get(
            food_class,
            {"small": 50.0, "medium": 100.0, "large": 150.0},
        )

        # Estimate size category from bounding box area
        x1, y1, x2, y2 = bbox
        area = (x2 - x1) * (y2 - y1)

        # Thresholds for 640x640 image
        image_area = 640 * 640
        relative_area = area / image_area

        if relative_area < 0.05:
            return portions["small"]
        if relative_area < 0.15:
            return portions["medium"]

        return portions["large"]

    def get_default_portions(self, food_class: str) -> Dict[str, float]:
        """Get default S/M/L portion sizes for a food class.

        Args:
            food_class: Food class name.

        Returns:
            Dictionary with small, medium, large gram values.
        """
        return self.DEFAULT_PORTIONS.get(
            food_class.lower(),
            {"small": 50.0, "medium": 100.0, "large": 150.0},
        )
