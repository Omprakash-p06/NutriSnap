"""FoodSAM-based food segmentation adapter for NutriSnap.

Wraps FoodSAM's multi-model pipeline (SAM + semantic classifier + detector)
behind a simple ``segment(image_path)`` interface.  Manages VRAM via sequential
load/run/unload strategy for GTX 1650 4 GB compatibility.

Usage::

    from nutrisnap.pipeline.segmenter import FoodSegmenter

    segmenter = FoodSegmenter(config_path="configs/pipeline/segmenter.yaml")
    result = segmenter.segment("path/to/meal.jpg")
    # result["masks"]         — list[np.ndarray] per-food boolean masks
    # result["combined_mask"] — np.ndarray single combined food mask
    # result["labels"]        — list[str] food class labels
    # result["scores"]        — list[float] confidence scores
"""
import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import yaml

from nutrisnap.utils.exceptions import InferenceError
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class FoodSegmenter:
    """Thin adapter around FoodSAM for food region segmentation.

    Handles:
    - Config-driven checkpoint paths
    - Sequential model loading for VRAM management
    - Graceful fallback to CPU
    - Combined food mask generation
    """

    def __init__(
        self,
        config_path: str | Path = "configs/pipeline/segmenter.yaml",
        device: Optional[str] = None,
    ):
        """Initialize FoodSegmenter.

        Args:
            config_path: Path to segmenter config YAML.
            device: Override device ('cuda', 'cpu', or None for auto).
        """
        self.config = self._load_config(config_path)
        self.device = self._resolve_device(device)
        self._sam_model = None
        self._validate_setup()

    def _load_config(self, config_path: str | Path) -> dict:
        """Load segmenter configuration from YAML."""
        path = Path(config_path)
        if not path.exists():
            raise InferenceError(f"Segmenter config not found: {path}")
        with open(path) as f:
            return yaml.safe_load(f)

    def _resolve_device(self, device_override: Optional[str]) -> torch.device:
        """Resolve compute device with auto-detection."""
        if device_override and device_override != "auto":
            return torch.device(device_override)

        cfg_device = self.config.get("inference", {}).get("device", "auto")
        if cfg_device != "auto":
            return torch.device(cfg_device)

        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(
                f"Using GPU: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB)"
            )
            return torch.device("cuda")
        else:
            logger.warning("CUDA not available — falling back to CPU (slow)")
            return torch.device("cpu")

    def _validate_setup(self) -> None:
        """Validate that FoodSAM directory and checkpoints exist."""
        model_cfg = self.config.get("model", {})
        sam_path = Path(model_cfg.get("sam_checkpoint", ""))
        foodsam_dir = Path(model_cfg.get("foodsam_dir", "third_party/FoodSAM"))

        if not foodsam_dir.exists():
            raise InferenceError(
                f"FoodSAM directory not found: {foodsam_dir}\n"
                f"Run: git submodule update --init --recursive"
            )

        if not sam_path.exists():
            raise InferenceError(
                f"SAM checkpoint not found: {sam_path}\n"
                f"Run: python scripts/setup_foodsam.py"
            )
        logger.info(f"FoodSAM validated: {foodsam_dir}")

    def _ensure_foodsam_importable(self) -> None:
        """Add FoodSAM to sys.path if not already importable."""
        foodsam_dir = str(
            Path(
                self.config.get("model", {}).get(
                    "foodsam_dir", "third_party/FoodSAM"
                )
            ).resolve()
        )
        if foodsam_dir not in sys.path:
            sys.path.insert(0, foodsam_dir)

    def _load_sam(self):
        """Load SAM model into memory."""
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

        model_cfg = self.config.get("model", {})
        inf_cfg = self.config.get("inference", {})

        sam_checkpoint = model_cfg.get("sam_checkpoint")
        sam_type = model_cfg.get("sam_model_type", "vit_h")

        logger.info(f"Loading SAM ({sam_type}) on {self.device}...")
        sam = sam_model_registry[sam_type](checkpoint=sam_checkpoint)
        sam.to(device=self.device)

        mask_generator = SamAutomaticMaskGenerator(
            sam,
            points_per_side=inf_cfg.get("points_per_side", 32),
            pred_iou_thresh=inf_cfg.get("pred_iou_thresh", 0.86),
            stability_score_thresh=inf_cfg.get("stability_score_thresh", 0.92),
        )
        return sam, mask_generator

    def _unload_model(self, model) -> None:
        """Unload a model and free VRAM."""
        vram_cfg = self.config.get("vram_management", {})
        del model
        if vram_cfg.get("empty_cache", True) and torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("VRAM cache cleared")

    def _resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Resize image if it exceeds max_image_dim to reduce VRAM usage."""
        max_dim = self.config.get("vram_management", {}).get("max_image_dim", 1024)
        h, w = image.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from ({h},{w}) to ({new_h},{new_w}) for VRAM")
        return image

    def segment(self, image_path: str | Path) -> dict:
        """Generate food masks for a meal image.

        Args:
            image_path: Path to input meal image (RGB).

        Returns:
            dict with keys:
                - masks: list[np.ndarray] — per-region boolean masks
                - labels: list[str] — food class labels (placeholder until
                  classifier integrated)
                - scores: list[float] — confidence scores from SAM
                - combined_mask: np.ndarray — single binary mask merging all
                  food regions
                - image_shape: tuple — original (H, W) of input image

        Raises:
            InferenceError: If segmentation fails.
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise InferenceError(f"Image not found: {image_path}")

        # Load image as RGB
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            raise InferenceError(f"Failed to read image: {image_path}")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        original_shape = image_rgb.shape[:2]

        # Resize for VRAM if needed
        image_for_sam = self._resize_if_needed(image_rgb)

        try:
            # Step 1: Load SAM and generate masks
            sam_model, mask_generator = self._load_sam()
            logger.info("Running SAM mask generation...")
            sam_output = mask_generator.generate(image_for_sam)

            # Sort by area (largest first), filter small noise masks
            sam_output = sorted(
                sam_output, key=lambda x: x["area"], reverse=True
            )
            min_area = (
                image_for_sam.shape[0] * image_for_sam.shape[1] * 0.01
            )  # 1% threshold
            sam_output = [m for m in sam_output if m["area"] >= min_area]

            # Extract masks and scores
            masks = [m["segmentation"].astype(bool) for m in sam_output]
            scores = [float(m["predicted_iou"]) for m in sam_output]

            # Placeholder labels — FoodSAM semantic classifier integration
            # is future work. For now label all regions as "food_region_N".
            labels = [f"food_region_{i}" for i in range(len(masks))]

            # Build combined mask
            if masks:
                combined = np.zeros(image_for_sam.shape[:2], dtype=bool)
                for m in masks:
                    combined |= m
                combined_mask = combined.astype(np.uint8) * 255
            else:
                combined_mask = np.zeros(
                    image_for_sam.shape[:2], dtype=np.uint8
                )
                logger.warning(
                    "No food masks generated — returning empty mask"
                )

            # Resize masks back to original resolution if we downscaled
            if image_for_sam.shape[:2] != original_shape:
                combined_mask = cv2.resize(
                    combined_mask,
                    (original_shape[1], original_shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
                masks = [
                    cv2.resize(
                        m.astype(np.uint8),
                        (original_shape[1], original_shape[0]),
                        interpolation=cv2.INTER_NEAREST,
                    ).astype(bool)
                    for m in masks
                ]

            logger.info(
                f"Segmentation complete: {len(masks)} regions found"
            )
            return {
                "masks": masks,
                "labels": labels,
                "scores": scores,
                "combined_mask": combined_mask,
                "image_shape": original_shape,
            }

        except InferenceError:
            raise
        except Exception as e:
            raise InferenceError(f"Segmentation failed: {e}") from e
        finally:
            # Always unload to free VRAM
            if "sam_model" in locals():
                self._unload_model(sam_model)
            if "mask_generator" in locals():
                self._unload_model(mask_generator)
