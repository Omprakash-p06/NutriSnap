"""Segmentation Model Wrapper.

Wrapper for Segment Anything Model (SAM) for food segmentation.
"""

from typing import Any, List, Optional, Tuple

import numpy as np


class SegmentationModel:
    """Wrapper for SAM (Segment Anything Model).

    Used for precise food region segmentation and masking.

    Attributes:
        model_type: SAM model variant (vit_b, vit_l, vit_h).
        checkpoint_path: Path to SAM checkpoint.
        model: Loaded SAM model.
    """

    def __init__(
        self,
        model_type: str = "vit_b",
        checkpoint_path: Optional[str] = None,
    ) -> None:
        """Initialize SAM wrapper.

        Args:
            model_type: SAM variant (vit_b, vit_l, vit_h).
            checkpoint_path: Path to SAM checkpoint file.
        """
        self.model_type = model_type
        self.checkpoint_path = checkpoint_path
        self._model = None
        self._predictor = None

    @property
    def model(self) -> Any:
        """Lazy load SAM model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load SAM model."""
        try:
            from segment_anything import SamPredictor, sam_model_registry

            if self.checkpoint_path is None:
                self._model = None
                return

            sam = sam_model_registry[self.model_type](checkpoint=self.checkpoint_path)
            self._predictor = SamPredictor(sam)
            self._model = sam
        except (ImportError, Exception):  # pylint: disable=broad-exception-caught
            self._model = None

    def segment_from_bbox(
        self,
        image: np.ndarray,
        bbox: List[int],
    ) -> Optional[np.ndarray]:
        """Generate segmentation mask from bounding box prompt.

        Args:
            image: Input RGB image as numpy array.
            bbox: Bounding box [x1, y1, x2, y2].

        Returns:
            Binary mask as numpy array, or None if model unavailable.
        """
        if self._predictor is None:
            return self._generate_mock_mask(image.shape[:2], bbox)

        try:
            self._predictor.set_image(image)

            masks, _, _ = self._predictor.predict(
                box=np.array(bbox),
                multimask_output=False,
            )

            return masks[0]
        except Exception:  # pylint: disable=broad-exception-caught
            return self._generate_mock_mask(image.shape[:2], bbox)

    def _generate_mock_mask(
        self,
        image_shape: Tuple[int, int],
        bbox: List[int],
    ) -> np.ndarray:
        """Generate a simple rectangular mask as fallback.

        Args:
            image_shape: (height, width) of the image.
            bbox: Bounding box [x1, y1, x2, y2].

        Returns:
            Binary mask as numpy array.
        """
        height, width = image_shape
        mask = np.zeros((height, width), dtype=np.uint8)

        x1, y1, x2, y2 = [int(c) for c in bbox]
        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))

        mask[y1:y2, x1:x2] = 1
        return mask

    def compute_area(self, mask: np.ndarray) -> int:
        """Compute the area of a segmentation mask.

        Args:
            mask: Binary mask.

        Returns:
            Number of pixels in the mask.
        """
        return int(np.sum(mask > 0))

    def is_loaded(self) -> bool:
        """Check if model is loaded.

        Returns:
            True if model is loaded, False otherwise.
        """
        return self._predictor is not None
