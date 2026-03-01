"""Image Processing Tool.

CrewAI tool for image preprocessing operations.
"""

from typing import Any, Dict

import cv2
import numpy as np

from backend.services.preprocessing import PreprocessingService


class ImageProcessingTool:
    """Tool for image preprocessing operations.

    Provides preprocessing capabilities for CrewAI agents.

    Attributes:
        service: Underlying preprocessing service.
    """

    name: str = "image_processor"
    description: str = "Preprocesses food images for AI model inference"

    def __init__(self, target_size: int = 640) -> None:
        """Initialize image processing tool.

        Args:
            target_size: Target image dimension.
        """
        self.service = PreprocessingService(target_size=target_size)

    def load_image(self, image_path: str) -> np.ndarray:
        """Load image from file path.

        Args:
            image_path: Path to image file.

        Returns:
            Image as BGR numpy array.
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        return image

    def preprocess(
        self,
        image: np.ndarray,
        enhance: bool = True,
    ) -> np.ndarray:
        """Preprocess image for model inference.

        Args:
            image: Input BGR image.
            enhance: Whether to apply enhancement.

        Returns:
            Preprocessed image.
        """
        return self.service.preprocess_for_inference(image, enhance=enhance)

    def run(self, image_path: str) -> Dict[str, Any]:
        """Run image preprocessing pipeline.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary with preprocessed image and metadata.
        """
        # Load image
        original = self.load_image(image_path)
        original_shape = original.shape

        # Preprocess
        processed = self.preprocess(original)

        return {
            "original_shape": original_shape,
            "processed_shape": processed.shape,
            "image": processed,
        }
