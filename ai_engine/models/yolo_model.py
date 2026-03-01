"""YOLOv8 Model Wrapper.

Wrapper for Ultralytics YOLOv8 object detection model.
"""

import os
from typing import Any, List

import numpy as np


class YOLOModel:
    """Wrapper for YOLOv8 object detection model.

    Attributes:
        model_path: Path to model weights.
        confidence_threshold: Minimum confidence for detections.
        iou_threshold: IoU threshold for NMS.
        image_size: Input image size.
        model: Loaded YOLO model.
    """

    def __init__(
        self,
        model_path: str = "./ml/weights/food_detection.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        image_size: int = 640,
    ) -> None:
        """Initialize YOLO model wrapper.

        Args:
            model_path: Path to YOLO weights file.
            confidence_threshold: Minimum detection confidence.
            iou_threshold: IoU threshold for NMS.
            image_size: Input image size.
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        self._model = None

    @property
    def model(self) -> Any:
        """Lazy load YOLO model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load YOLO model from weights file."""
        try:
            from ultralytics import YOLO  # pylint: disable=import-outside-toplevel

            if os.path.exists(self.model_path):
                self._model = YOLO(self.model_path)
            else:
                # Use pretrained nano model as fallback
                self._model = YOLO("yolov8n.pt")
        except ImportError:
            self._model = None

    def predict(
        self,
        image: np.ndarray,
        verbose: bool = False,
    ) -> List[dict]:
        """Run inference on an image.

        Args:
            image: Input image as numpy array (RGB).
            verbose: Whether to print verbose output.

        Returns:
            List of detection dictionaries.
        """
        if self.model is None:
            return []

        results = self.model(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            verbose=verbose,
        )

        detections = []
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                detections.append(
                    {
                        "class_id": int(boxes.cls[i]),
                        "class_name": result.names[int(boxes.cls[i])],
                        "confidence": float(boxes.conf[i]),
                        "bbox_xyxy": boxes.xyxy[i].tolist(),
                        "bbox_xywh": boxes.xywh[i].tolist(),
                    }
                )

        return detections

    def get_class_names(self) -> List[str]:
        """Get list of class names.

        Returns:
            List of class name strings.
        """
        if self.model is None:
            return ["rice", "dal", "paneer", "roti"]
        return list(self.model.names.values())
