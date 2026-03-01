"""Image Preprocessing Service.

Digital Image Processing pipeline for food images.
"""

# pylint: disable=no-member

from typing import Tuple

import cv2
import numpy as np
from numpy.typing import NDArray


class PreprocessingService:
    """Service for image preprocessing (DIP pipeline).

    Attributes:
        target_size: Target image size for model input.
    """

    def __init__(self, target_size: int = 640) -> None:
        """Initialize preprocessing service.

        Args:
            target_size: Target image dimension (width and height).
        """
        self.target_size = target_size

    def resize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Resize image to target size.

        Args:
            image: Input image as numpy array.

        Returns:
            Resized image.
        """
        return cv2.resize(
            image,
            (self.target_size, self.target_size),
            interpolation=cv2.INTER_LINEAR,
        )

    def normalize(self, image: NDArray[np.uint8]) -> NDArray[np.float32]:
        """Normalize pixel values to [0, 1] range.

        Args:
            image: Input image as uint8 array.

        Returns:
            Normalized image as float32 array.
        """
        return image.astype(np.float32) / 255.0

    def bgr_to_rgb(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Convert BGR (OpenCV) to RGB color space.

        Args:
            image: BGR image.

        Returns:
            RGB image.
        """
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def denoise(
        self,
        image: NDArray[np.uint8],
        strength: int = 10,
    ) -> NDArray[np.uint8]:
        """Apply noise reduction using non-local means denoising.

        Args:
            image: Input image.
            strength: Denoising strength.

        Returns:
            Denoised image.
        """
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            strength,
            strength,
            7,
            21,
        )

    def apply_clahe(
        self,
        image: NDArray[np.uint8],
        clip_limit: float = 2.0,
        tile_size: Tuple[int, int] = (8, 8),
    ) -> NDArray[np.uint8]:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Args:
            image: Input BGR image.
            clip_limit: Contrast limiting threshold.
            tile_size: Size of grid for histogram equalization.

        Returns:
            Enhanced image.
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
        l_enhanced = clahe.apply(l_channel)

        # Merge channels and convert back to BGR
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    def white_balance(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Apply gray-world white balance correction.

        Args:
            image: Input BGR image.

        Returns:
            White-balanced image.
        """
        result = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        result[:, :, 1] = result[:, :, 1] - (
            (avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1
        )
        result[:, :, 2] = result[:, :, 2] - (
            (avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1
        )
        result = np.clip(result, 0, 255).astype(np.uint8)
        return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

    def sharpen(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Apply unsharp masking for sharpening.

        Args:
            image: Input image.

        Returns:
            Sharpened image.
        """
        gaussian = cv2.GaussianBlur(image, (0, 0), 3)
        return cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)

    def detect_edges(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        """Detect edges using Canny edge detector.

        Args:
            image: Input image.

        Returns:
            Edge map.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, 50, 150)

    def preprocess_for_inference(
        self,
        image: NDArray[np.uint8],
        enhance: bool = True,
    ) -> NDArray[np.float32]:
        """Full preprocessing pipeline for model inference.

        Args:
            image: Input BGR image.
            enhance: Whether to apply enhancement steps.

        Returns:
            Preprocessed image ready for model input.
        """
        # Resize
        processed = self.resize(image)

        # Enhancement (optional)
        if enhance:
            processed = self.apply_clahe(processed)
            processed = self.white_balance(processed)

        # Color space conversion
        processed = self.bgr_to_rgb(processed)

        # Normalize
        return self.normalize(processed)

    def preprocess_for_training(
        self,
        image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        """Preprocessing pipeline for training data.

        Args:
            image: Input BGR image.

        Returns:
            Preprocessed uint8 image for augmentation.
        """
        # Resize
        processed = self.resize(image)

        # Enhancement
        processed = self.apply_clahe(processed)
        processed = self.white_balance(processed)

        # Color space conversion
        return self.bgr_to_rgb(processed)
