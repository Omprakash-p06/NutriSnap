"""Image preprocessor for the NutriSnap pipeline.

Handles image enhancement, JPEG artifact reduction, and sharpening
to improve detection accuracy on compressed high-resolution images.
"""

from pathlib import Path
from typing import Union, Optional

import cv2
import numpy as np
from PIL import Image

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

class ImagePreprocessor:
    """Preprocesses images to enhance quality for detection and segmentation."""

    @staticmethod
    def enhance_image(
        image: Union[str, Path, np.ndarray, Image.Image]
    ) -> np.ndarray:
        """Apply smart enhancement to reduce artifacts and sharpen edges.
        
        Args:
            image: Input image in various formats.
            
        Returns:
            Enhanced image as a numpy array (RGB).
        """
        # Convert to numpy RGB
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            img = np.array(image.convert("RGB"))
        elif isinstance(image, np.ndarray):
            img = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # 1. Reduce JPEG artifacts using a slight bilateral filter
        # It preserves edges while smoothing flat areas where artifacts are visible
        enhanced = cv2.bilateralFilter(img, d=5, sigmaColor=50, sigmaSpace=50)

        # 2. Sharpen edges using unsharp masking
        gaussian_3 = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        enhanced = cv2.addWeighted(enhanced, 1.5, gaussian_3, -0.5, 0)

        # 3. Contrast enhancement (CLAHE) - Optional but good for muddy features
        lab = cv2.cvtColor(enhanced, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)

        logger.info("Image enhancement complete (Bilateral Filter + Unsharp Mask + CLAHE)")
        return enhanced

    @staticmethod
    def enhance_compressed_image(
        image: np.ndarray,
        file_size_bytes: Optional[int] = None,
    ) -> np.ndarray:
        """Upscale and sharpen images that are heavily JPEG-compressed.

        High-resolution images stored at very small file sizes (e.g. 4K photo
        at 130 KB) lose most texture due to extreme JPEG quantisation.  This
        function detects such images and applies a 2× Lanczos upscale followed
        by unsharp masking to restore some of the lost detail.

        Args:
            image: Input image as an RGB numpy array.
            file_size_bytes: Original file size in bytes (used to detect
                             heavy compression).  If None, the check is
                             skipped and the image is returned unchanged.

        Returns:
            Upscaled + sharpened image if it was detected as heavily compressed,
            otherwise the original image unchanged.
        """
        if file_size_bytes is None:
            return image

        h, w = image.shape[:2]
        pixel_count = h * w

        # Heuristic: large pixel footprint but tiny file → heavily compressed
        # Threshold: > 2 MP with < 500 KB on disk
        is_compressed = pixel_count > 2_000_000 and file_size_bytes < 500 * 1024

        if not is_compressed:
            return image

        logger.info(
            f"Detected heavily compressed image ({w}x{h}, {file_size_bytes/1024:.0f} KB). "
            "Applying 2× Lanczos upscale + unsharp mask."
        )

        # 2× upscale via high-quality Lanczos interpolation
        upscaled = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)

        # Unsharp masking to recover edge detail
        blurred = cv2.GaussianBlur(upscaled, (0, 0), 3)
        sharpened = cv2.addWeighted(upscaled, 1.5, blurred, -0.5, 0)

        logger.info(f"Upscaled to {w*2}x{h*2} for better detection coverage.")
        return sharpened

    def preprocess_for_pipeline(
        self, 
        image_path: Union[str, Path], 
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Enhance image and optionally save to a temporary file.
        
        Args:
            image_path: Path to the original image.
            output_path: Where to save enhanced image. If None, uses a temporary path.
            
        Returns:
            Path to the enhanced image.
        """
        image_path = Path(image_path)
        file_size = image_path.stat().st_size if image_path.exists() else None

        # Base enhancement (bilateral filter, unsharp mask, CLAHE)
        enhanced = self.enhance_image(image_path)

        # Additional upscaling pass for heavily compressed images
        enhanced = self.enhance_compressed_image(enhanced, file_size_bytes=file_size)

        # Downscale to max inference dimension (1024) to prevent CUDA OOM on 4GB GPUs
        MAX_DIM = 1024
        h, w = enhanced.shape[:2]
        if w > MAX_DIM or h > MAX_DIM:
            scale = MAX_DIM / max(h, w)
            enhanced = cv2.resize(enhanced, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
            logger.info(f"Downscaled image for inference to {enhanced.shape[1]}x{enhanced.shape[0]}")

        if output_path is None:
            output_path = image_path.parent / f"{image_path.stem}_enhanced{image_path.suffix}"
        
        output_path = Path(output_path)
        
        # Save enhanced image
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), enhanced_bgr)
        
        logger.info(f"Enhanced image saved to {output_path}")
        return str(output_path)
