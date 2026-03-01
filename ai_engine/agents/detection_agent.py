"""Detection Agent.

YOLOv8-based food detection agent.
"""

import os
from typing import Any, Dict, List, Optional


class DetectionAgent:
    """Agent for food detection using YOLOv8.

    Attributes:
        model_path: Path to YOLOv8 weights file.
        confidence_threshold: Minimum confidence for detections.
        model: Loaded YOLO model (lazy loaded).
        classes: List of food class names.
    """

    # Food classes matching data.yaml order
    FOOD_CLASSES = ["dal", "paneer", "rice", "roti"]

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ) -> None:
        """Initialize detection agent.

        Args:
            model_path: Path to YOLOv8 weights file.
            confidence_threshold: Minimum detection confidence (0-1).
        """
        self.model_path = model_path or "./ml/weights/yolov8_food.pt"
        self.confidence_threshold = confidence_threshold
        self._model = None
        self.classes = self.FOOD_CLASSES.copy()

    @property
    def model(self) -> Any:
        """Lazy load YOLO model.

        Returns:
            Loaded YOLO model.
        """
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load the YOLO model from weights file."""
        if not os.path.exists(self.model_path):
            # Fall back to pretrained model for development
            try:
                from ultralytics import YOLO  # pylint: disable=import-outside-toplevel

                self._model = YOLO("yolov8n.pt")  # Use nano pretrained
            except ImportError:
                self._model = None
        else:
            try:
                from ultralytics import YOLO  # pylint: disable=import-outside-toplevel

                self._model = YOLO(self.model_path)
            except ImportError:
                self._model = None

    def detect(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect food items in an image.

        Args:
            image_path: Path to the image file.

        Returns:
            List of detection dictionaries with class, confidence, bbox.
        """
        # If model is not available, return mock data for development
        if self.model is None:
            return self._mock_detection()

        # Run YOLO inference
        results = self.model(image_path, verbose=False, device="cpu")

        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                confidence = float(boxes.conf[i])
                if confidence < self.confidence_threshold:
                    continue

                class_id = int(boxes.cls[i])
                bbox = boxes.xyxy[i].tolist()

                # Map class ID to name
                if class_id < len(self.classes):
                    class_name = self.classes[class_id]
                else:
                    class_name = f"food_{class_id}"

                detections.append(
                    {
                        "class": class_name,
                        "class_id": class_id,
                        "confidence": round(confidence, 3),
                        "bbox": [int(x) for x in bbox],
                    }
                )

        return detections

    def _mock_detection(self) -> List[Dict[str, Any]]:
        """Generate mock detection data for development.

        Returns:
            List of mock detections.
        """
        return [
            {
                "class": "rice",
                "class_id": 0,
                "confidence": 0.92,
                "bbox": [100, 100, 300, 300],
            },
            {
                "class": "dal",
                "class_id": 1,
                "confidence": 0.88,
                "bbox": [320, 100, 500, 280],
            },
        ]

    def get_classes(self) -> List[str]:
        """Get list of detectable food classes.

        Returns:
            List of food class names.
        """
        return self.classes.copy()
