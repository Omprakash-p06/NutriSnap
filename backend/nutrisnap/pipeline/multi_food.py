"""Multi-food detection pipeline using YOLOv8.

Uses YOLOv8 for detecting multiple food items in a meal image,
providing bounding boxes that can be used as prompts for SAM 2 segmentation.

Usage::

    from nutrisnap.pipeline.multi_food import MultiFoodDetector

    detector = MultiFoodDetector()
    results = detector.detect("path/to/meal.jpg")
    # results = [{"label": "pizza", "box": [x1, y1, x2, y2], "score": 0.95}, ...]
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
import torch
from ultralytics import YOLO

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


# COCO food-related classes - YOLOv8 pretrained on COCO includes many food items
FOOD_CLASSES = {
    0: "person",  # Not food, but included for context
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports_ball",
    33: "kite",
    34: "baseball_bat",
    35: "baseball_glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis_racket",
    39: "bottle",
    40: "wine_glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot_dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "couch",
    58: "potted_plant",
    59: "bed",
    60: "dining_table",
    61: "toilet",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell_phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "refrigerator",
    72: "book",
    73: "clock",
    74: "vase",
    75: "scissors",
    76: "teddy_bear",
    77: "hair_dryer",
    78: "toothbrush",
}


# Classes that are likely food items in a meal context
LIKELY_FOOD_CLASSES = {46, 47, 48, 49, 50, 51, 52, 53, 54, 55}


class MultiFoodDetector:
    """Multi-food detector using YOLOv8.

    Detects food items in meal images using YOLOv8 pretrained on COCO.
    Returns bounding boxes suitable for SAM 2 box-prompted segmentation.
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        device: Optional[str] = None,
        confidence_threshold: float = 0.25,
    ):
        """Initialize MultiFoodDetector.

        Args:
            model_name: YOLOv8 model to use (yolov8n.pt, yolov8s.pt, etc.)
            device: Override device ('cuda', 'cpu', or None for auto).
            confidence_threshold: Minimum confidence for detections.
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold

        # Resolve device
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        # Load model
        logger.info(f"Loading YOLOv8 ({model_name}) on {self.device}...")
        self.model = YOLO(model_name)
        logger.info("YOLOv8 loaded successfully")

    def detect(
        self,
        image: Union[str, Path, np.ndarray],
        max_detections: int = 10,
    ) -> list[dict]:
        """Detect food items in a meal image.

        Args:
            image: Path to image file or numpy array (RGB).
            max_detections: Maximum number of detections to return.

        Returns:
            List of detections, each with:
                - label: str - class name
                - box: list[int] - [x1, y1, x2, y2] in pixel coordinates
                - score: float - confidence score
                - class_id: int - COCO class ID
        """
        # Run inference
        results = self.model.predict(
            image,
            device=self.device,
            conf=self.confidence_threshold,
            max_det=max_detections,
            verbose=False,
        )

        if not results or len(results) == 0:
            return []

        result = results[0]
        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return []

        detections = []
        for i in range(len(boxes)):
            box = boxes[i]
            class_id = int(box.cls.cpu().numpy()[0])
            conf = float(box.conf.cpu().numpy()[0])

            # Get coordinates
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])

            label = FOOD_CLASSES.get(class_id, f"class_{class_id}")

            detections.append(
                {
                    "label": label,
                    "box": [x1, y1, x2, y2],
                    "score": conf,
                    "class_id": class_id,
                }
            )

        logger.info(f"Detected {len(detections)} items")
        return detections

    def detect_food_only(
        self,
        image: Union[str, Path, np.ndarray],
        max_detections: int = 10,
    ) -> list[dict]:
        """Detect only food-related items.

        Filters to likely food classes for more relevant detection.

        Args:
            image: Path to image file or numpy array (RGB).
            max_detections: Maximum number of detections.

        Returns:
            List of food detections.
        """
        all_detections = self.detect(image, max_detections * 2)

        # Filter to likely food items
        food_detections = [
            d for d in all_detections if d["class_id"] in LIKELY_FOOD_CLASSES
        ]

        return food_detections[:max_detections]

    @staticmethod
    def normalize_boxes(
        boxes: list[list[int]], image_size: tuple[int, int]
    ) -> list[list[float]]:
        """Normalize boxes to [0, 1] range for SAM 2 prompts.

        Args:
            boxes: List of [x1, y1, x2, y2] pixel coordinates.
            image_size: (width, height) of the image.

        Returns:
            List of normalized [x1, y1, x2, y2] in [0, 1] range.
        """
        width, height = image_size
        normalized = []
        for box in boxes:
            x1_norm = box[0] / width
            y1_norm = box[1] / height
            x2_norm = box[2] / width
            y2_norm = box[3] / height
            normalized.append([x1_norm, y1_norm, x2_norm, y2_norm])
        return normalized

    @staticmethod
    def denormalize_boxes(
        boxes: list[list[float]], image_size: tuple[int, int]
    ) -> list[list[int]]:
        """Convert normalized boxes back to pixel coordinates.

        Args:
            boxes: List of normalized [x1, y1, x2, y2] in [0, 1] range.
            image_size: (width, height) of the image.

        Returns:
            List of pixel [x1, y1, x2, y2] coordinates.
        """
        width, height = image_size
        denormalized = []
        for box in boxes:
            x1 = int(box[0] * width)
            y1 = int(box[1] * height)
            x2 = int(box[2] * width)
            y2 = int(box[3] * height)
            denormalized.append([x1, y1, x2, y2])
        return denormalized

    def unload(self) -> None:
        """Unload model from GPU to free VRAM."""
        if hasattr(self, "model"):
            del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("YOLOv8 model unloaded")
