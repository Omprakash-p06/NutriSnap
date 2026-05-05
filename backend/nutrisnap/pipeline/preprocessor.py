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
        enhanced = self.enhance_image(image_path)
        
        if output_path is None:
            output_path = image_path.parent / f"{image_path.stem}_enhanced{image_path.suffix}"
        
        output_path = Path(output_path)
        
        # Save enhanced image
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), enhanced_bgr)
        
        logger.info(f"Enhanced image saved to {output_path}")
        return str(output_path)
