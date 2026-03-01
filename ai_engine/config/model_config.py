"""Model Configuration.

Configuration settings for AI models.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class ModelConfig:
    """Configuration for AI models.

    Attributes:
        base_path: Base path for model weights.
        yolo_model_name: YOLO model filename.
        portion_model_name: Portion model filename.
        confidence_threshold: Detection confidence threshold.
        iou_threshold: NMS IoU threshold.
        image_size: Input image size.
        food_classes: List of food class names.
    """

    base_path: str = "./ml/weights/"
    yolo_model_name: str = "food_detection.pt"
    portion_model_name: str = "portion_model.joblib"

    # Detection settings
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    image_size: int = 640

    # Food classes
    food_classes: List[str] = field(
        default_factory=lambda: ["rice", "dal", "paneer", "roti"]
    )

    @property
    def yolo_model_path(self) -> str:
        """Get full path to YOLO model."""
        return os.path.join(self.base_path, self.yolo_model_name)

    @property
    def portion_model_path(self) -> str:
        """Get full path to portion model."""
        return os.path.join(self.base_path, self.portion_model_name)

    @classmethod
    def from_env(cls) -> "ModelConfig":
        """Create config from environment variables.

        Returns:
            ModelConfig instance.
        """
        return cls(
            base_path=os.getenv("MODEL_PATH", "./ml/weights/"),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
            image_size=int(os.getenv("IMAGE_SIZE", "640")),
        )
