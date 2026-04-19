"""GLPN-based depth estimation adapter for NutriSnap.

Provides DepthEstimatorGLPN for monocular depth estimation.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
import torch
import yaml
from PIL import Image
from transformers import GLPNForDepthEstimation, GLPNImageProcessor

from nutrisnap.utils.exceptions import InferenceError
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class DepthEstimatorGLPN:
    """GLPN depth estimation adapter."""

    def __init__(
        self,
        config_path: Union[str, Path] = "configs/pipeline/depth.yaml",
        device: Optional[str] = None,
    ):
        """Initialize GLPN depth estimator.

        Args:
            config_path: Path to config YAML.
            device: Override device ('cuda', 'cpu', or None for auto).
        """
        self.config = self._load_config(config_path)
        self.device_str = self._resolve_device(device)
        self.device = torch.device(self.device_str)

        model_cfg = self.config.get("model", {})
        model_id = model_cfg.get("model_id", "vinvino02/glpn-nyu")
        logger.info(f"Loading GLPN ({model_id}) on {self.device_str}...")

        self.processor = GLPNImageProcessor.from_pretrained(model_id)
        self.model = GLPNForDepthEstimation.from_pretrained(model_id).to(self.device)
        logger.info("GLPN loaded successfully")

    def _load_config(self, config_path: Union[str, Path]) -> dict:
        path = Path(config_path)
        if not path.exists():
            return {}
        with open(path) as f:
            return yaml.safe_load(f)

    def _resolve_device(self, device_override: Optional[str]) -> str:
        if device_override and device_override != "auto":
            return device_override
        cfg_device = self.config.get("inference", {}).get("device", "auto")
        if cfg_device != "auto":
            return cfg_device
        return "cuda" if torch.cuda.is_available() else "cpu"

    def estimate(self, image: Union[str, Path, np.ndarray, Image.Image]) -> np.ndarray:
        """Estimate depth map from image.

        Args:
            image: Input image (path, numpy array, or PIL).

        Returns:
            Normalized depth map (float32, 0-1), same shape as input.
        """
        if isinstance(image, (str, Path)):
            image_pil = Image.open(image).convert("RGB")
        elif isinstance(image, np.ndarray):
            image_pil = Image.fromarray(image).convert("RGB")
        elif isinstance(image, Image.Image):
            image_pil = image.convert("RGB")
        else:
            raise InferenceError(f"Unsupported image type: {type(image)}")

        original_size = (image_pil.height, image_pil.width)

        try:
            inputs = self.processor(images=image_pil, return_tensors="pt").to(
                self.device
            )
            with torch.no_grad():
                outputs = self.model(**inputs)
                predicted_depth = outputs.predicted_depth

            # Post-process: interpolate to original size
            prediction = torch.nn.functional.interpolate(
                predicted_depth.unsqueeze(1),
                size=original_size,
                mode="bicubic",
                align_corners=False,
            ).squeeze()

            depth_map = prediction.cpu().numpy()

            # Normalize to 0-1
            depth_min = depth_map.min()
            depth_max = depth_map.max()
            if depth_max > depth_min:
                depth_map = (depth_map - depth_min) / (depth_max - depth_min)
            else:
                depth_map = np.zeros_like(depth_map)

            return depth_map.astype(np.float32)

        except Exception as e:
            raise InferenceError(f"GLPN depth estimation failed: {e}") from e
