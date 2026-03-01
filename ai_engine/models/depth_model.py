"""Depth Estimation Model Wrapper.

Wrapper for Depth Anything V2 depth estimation model.
"""

from typing import Any, Optional

import numpy as np


class DepthModel:
    """Wrapper for Depth Anything V2 depth estimation.

    Used for volumetric portion estimation by analyzing depth maps.

    Attributes:
        model_name: Name of the depth model variant.
        model: Loaded depth model.
    """

    def __init__(
        self,
        model_name: str = "depth-anything-v2-small",
    ) -> None:
        """Initialize depth model wrapper.

        Args:
            model_name: Depth Anything V2 model variant.
        """
        self.model_name = model_name
        self._model = None
        self._processor = None

    @property
    def model(self) -> Any:
        """Lazy load depth model."""
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """Load Depth Anything V2 model."""
        try:
            from transformers import pipeline

            self._model = pipeline(
                "depth-estimation",
                model=f"depth-anything/{self.model_name}",
                device=-1,
            )
        except (ImportError, Exception):
            self._model = None

    def predict(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Estimate depth map from RGB image.

        Args:
            image: Input RGB image as numpy array.

        Returns:
            Depth map as numpy array, or None if model unavailable.
        """
        if self.model is None:
            return None

        try:
            from PIL import Image

            pil_image = Image.fromarray(image)
            result = self.model(pil_image)
            return np.array(result["depth"])
        except Exception:
            return None

    def get_relative_depth(
        self,
        depth_map: np.ndarray,
        bbox: list,
    ) -> float:
        """Get relative depth for a region.

        Args:
            depth_map: Full depth map.
            bbox: Bounding box [x1, y1, x2, y2].

        Returns:
            Mean relative depth for the region.
        """
        x1, y1, x2, y2 = [int(c) for c in bbox]
        region = depth_map[y1:y2, x1:x2]

        if not region.size:
            return 0.5

        return float(np.mean(region))

    def is_loaded(self) -> bool:
        """Check if model is loaded.

        Returns:
            True if model is loaded, False otherwise.
        """
        return self.model is not None
