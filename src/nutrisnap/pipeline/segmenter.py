"""FoodSAM-based food segmentation adapter for NutriSnap.

Wraps FoodSAM's multi-model pipeline (SAM + semantic classifier + detector)
behind a simple ``segment(image)`` interface.  Manages VRAM via sequential
load/run/unload strategy for GTX 1650 4 GB compatibility.

Usage::

    from nutrisnap.pipeline.segmenter import FoodSegmenter

    segmenter = FoodSegmenter(config_path="configs/pipeline/segmenter.yaml")
    result = segmenter.segment("path/to/meal.jpg")
    # or
    result = segmenter.segment(image_numpy_rgb)

    # result["masks"]         — list[np.ndarray] per-food boolean masks
    # result["combined_mask"] — np.ndarray single combined food mask
    # result["labels"]        — list[str] food class labels
    # result["scores"]        — list[float] confidence scores
"""

import sys
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
import torch
import yaml
from PIL import Image
from transformers import AutoProcessor, Sam2Model, pipeline

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
        persistent: bool = True,
    ):
        """Initialize FoodSegmenter.

        Args:
            config_path: Path to segmenter config YAML.
            device: Override device ('cuda', 'cpu', or None for auto).
            persistent: If True, keep models in VRAM between calls.
        """
        self.config = self._load_config(config_path)
        self.device = self._resolve_device(device)
        self.persistent = persistent
        self._sam_model = None
        self._mask_generator = None
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
                self.config.get("model", {}).get("foodsam_dir", "third_party/FoodSAM")
            ).resolve()
        )
        if foodsam_dir not in sys.path:
            sys.path.insert(0, foodsam_dir)

    def _load_sam(self):
        """Load SAM model into memory."""
        if self.persistent and self._sam_model is not None:
            return self._sam_model, self._mask_generator

        self._ensure_foodsam_importable()
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
        if self.persistent:
            self._sam_model = sam
            self._mask_generator = mask_generator

        return sam, mask_generator

    def unload(self) -> None:
        """Unload models and free VRAM manually."""
        if self._sam_model is not None:
            self._unload_model(self._sam_model)
            self._sam_model = None
        if self._mask_generator is not None:
            self._unload_model(self._mask_generator)
            self._mask_generator = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("VRAM cache cleared")

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

    def segment(self, image: Union[str, Path, np.ndarray]) -> dict:
        """Generate food masks for a meal image.

        Args:
            image: Path to input meal image (RGB) OR numpy array (RGB).

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
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise InferenceError(f"Image not found: {image_path}")
            # Load image as RGB
            image_bgr = cv2.imread(str(image_path))
            if image_bgr is None:
                raise InferenceError(f"Failed to read image: {image_path}")
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        else:
            # Assume it's already an RGB numpy array
            image_rgb = image

        original_shape = image_rgb.shape[:2]

        # Resize for VRAM if needed
        image_for_sam = self._resize_if_needed(image_rgb)

        try:
            # Step 1: Load SAM and generate masks
            sam_model, mask_generator = self._load_sam()
            logger.info("Running SAM mask generation...")
            sam_output = mask_generator.generate(image_for_sam)

            # Sort by area (largest first), filter small noise masks
            sam_output = sorted(sam_output, key=lambda x: x["area"], reverse=True)
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
                combined_mask = np.zeros(image_for_sam.shape[:2], dtype=np.uint8)
                logger.warning("No food masks generated — returning empty mask")

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

            logger.info(f"Segmentation complete: {len(masks)} regions found")
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


class FoodSegmenterSAM2:
    """SAM 2-based food segmentation adapter.

    Uses facebook/sam2-hiera-tiny/small via Hugging Face Transformers.
    """

    def __init__(
        self,
        model_id: str = "facebook/sam2-hiera-tiny",
        device: Optional[str] = None,
    ):
        """Initialize SAM 2 segmenter.

        Args:
            model_id: Hugging Face model ID.
            device: Override device ('cuda', 'cpu', or None for auto).
        """
        self.device_str = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.device = torch.device(self.device_str)
        self.model_id = model_id

        # Use pipeline for automatic mask generation (handles point grids)
        # Internally uses Sam2Model and Sam2Processor/ImageProcessor
        logger.info(f"Loading SAM 2 ({model_id}) on {self.device_str}...")

        # Explicitly load to satisfy requirement and ensure device placement
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = Sam2Model.from_pretrained(model_id).to(self.device)

        self.pipe = pipeline(
            "mask-generation",
            model=self.model,
            image_processor=self.processor.image_processor,
            device=0 if self.device_str == "cuda" else -1,
        )
        logger.info("SAM 2 loaded successfully")

    def unload(self):
        """Unload model from GPU to free VRAM."""
        if hasattr(self, "model"):
            self.model.cpu()
            del self.model
        if hasattr(self, "pipe"):
            del self.pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("SAM 2 model unloaded from GPU")

    def segment(self, image: Union[str, Path, np.ndarray]) -> dict:
        """Generate food masks using SAM 2.

        Args:
            image: Path or numpy array (RGB).

        Returns:
            Standardized segmentation dict.
        """
        if isinstance(image, (str, Path)):
            img_path = Path(image)
            if not img_path.exists():
                raise InferenceError(f"Image not found: {img_path}")
            image_pil = Image.open(img_path).convert("RGB")
            original_shape = (image_pil.height, image_pil.width)
        elif isinstance(image, np.ndarray):
            image_pil = Image.fromarray(image)
            original_shape = image.shape[:2]
        else:
            raise InferenceError(f"Unsupported image type: {type(image)}")

        try:
            # Use lower point density for speed/VRAM
            outputs = self.pipe(image_pil, points_per_batch=64, points_per_crop=8)

            raw_masks = outputs.get("masks", [])
            raw_scores = outputs.get("scores", [])

            # Convert tensors/PIL to numpy boolean masks
            masks: list[np.ndarray] = []
            scores: list[float] = []
            for m in raw_masks:
                if isinstance(m, torch.Tensor):
                    masks.append(m.cpu().numpy().astype(bool))
                else:
                    masks.append(np.array(m).astype(bool))

            for s in raw_scores:
                scores.append(float(s))

            # Sort by area
            mask_data = sorted(
                zip(masks, scores), key=lambda x: np.sum(x[0]), reverse=True
            )

            final_masks: list[np.ndarray] = []
            final_scores: list[float] = []

            if mask_data:
                for m, s in mask_data:
                    final_masks.append(m)
                    final_scores.append(s)

            # Filter small noise (less than 1% of image area)
            min_area = original_shape[0] * original_shape[1] * 0.01
            filtered_masks: list[np.ndarray] = []
            filtered_scores: list[float] = []

            for m, s in zip(final_masks, final_scores):
                if np.sum(m) >= min_area:
                    filtered_masks.append(m)
                    filtered_scores.append(s)

            labels = [f"food_region_{i}" for i in range(len(filtered_masks))]

            if filtered_masks:
                combined = np.zeros(original_shape, dtype=bool)
                for m in filtered_masks:
                    combined |= m
                combined_mask = combined.astype(np.uint8) * 255
            else:
                combined_mask = np.zeros(original_shape, dtype=np.uint8)

            return {
                "masks": filtered_masks,
                "labels": labels,
                "scores": filtered_scores,
                "combined_mask": combined_mask,
                "image_shape": original_shape,
            }

        except Exception as e:
            raise InferenceError(f"SAM 2 segmentation failed: {e}") from e

    def segment_batch(
        self,
        image_paths: list[Union[str, Path]],
        batch_size: int = 8,
        target_size: tuple[int, int] = (512, 512),
    ) -> list[dict]:
        """Generate food masks for a batch of images using SAM 2.

        Args:
            image_paths: List of paths to input images.
            batch_size: Number of images to process simultaneously.
            target_size: Resolution to resize inputs to before processing (w, h).

        Returns:
            List of standardized segmentation dicts.
        """
        all_results = []

        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i : i + batch_size]
            batch_images = []
            original_sizes = []

            for path in batch_paths:
                img_path = Path(path)
                if not img_path.exists():
                    logger.error(f"Image not found for batch processing: {img_path}")
                    # Create a dummy image to maintain batch alignment if a file is missing
                    img = Image.new("RGB", target_size)
                    original_sizes.append(target_size)
                else:
                    img = Image.open(img_path).convert("RGB")
                    original_sizes.append((img.height, img.width))

                img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                batch_images.append(img_resized)

            try:
                # The transformers pipeline for SAM 2 has a bug with batch_size > 1
                # so we iterate through the resized batch images sequentially.
                # Because the images are resized to 512x512, this is still very fast.
                outputs = []
                for img in batch_images:
                    # By reducing points_per_crop to 8 (64 points) instead of 16 (256)
                    # and points_per_batch to 64, we massively speed up inference and save VRAM
                    outputs.append(
                        self.pipe(img, points_per_batch=64, points_per_crop=8)
                    )

                # If batch_size=1, the pipeline might return a single dict instead of a list of dicts
                if not isinstance(outputs, list):
                    outputs = [outputs]

                for j, out in enumerate(outputs):
                    original_shape = original_sizes[j]
                    raw_masks = out.get("masks", [])
                    raw_scores = out.get("scores", [])

                    masks: list[np.ndarray] = []
                    scores: list[float] = []
                    for m in raw_masks:
                        if isinstance(m, torch.Tensor):
                            masks.append(m.cpu().numpy().astype(bool))
                        else:
                            masks.append(np.array(m).astype(bool))

                    for s in raw_scores:
                        scores.append(float(s))

                    mask_data = sorted(
                        zip(masks, scores), key=lambda x: np.sum(x[0]), reverse=True
                    )
                    final_masks = [m for m, s in mask_data]
                    final_scores = [s for m, s in mask_data]

                    # Filter small noise (less than 1% of resized image area)
                    min_area = target_size[0] * target_size[1] * 0.01
                    filtered_masks: list[np.ndarray] = []
                    filtered_scores: list[float] = []

                    for m, s in zip(final_masks, final_scores):
                        if np.sum(m) >= min_area:
                            filtered_masks.append(m)
                            filtered_scores.append(s)

                    labels = [
                        f"food_region_{idx}" for idx in range(len(filtered_masks))
                    ]

                    if filtered_masks:
                        combined = np.zeros(
                            (target_size[1], target_size[0]), dtype=bool
                        )
                        for m in filtered_masks:
                            combined |= m
                        combined_mask = combined.astype(np.uint8) * 255
                    else:
                        combined_mask = np.zeros(
                            (target_size[1], target_size[0]), dtype=np.uint8
                        )

                    # Resize masks back to original resolution
                    combined_mask = cv2.resize(
                        combined_mask,
                        (original_shape[1], original_shape[0]),
                        interpolation=cv2.INTER_NEAREST,
                    )

                    resized_masks = []
                    for m in filtered_masks:
                        resized_m = cv2.resize(
                            m.astype(np.uint8),
                            (original_shape[1], original_shape[0]),
                            interpolation=cv2.INTER_NEAREST,
                        ).astype(bool)
                        resized_masks.append(resized_m)

                    all_results.append(
                        {
                            "masks": resized_masks,
                            "labels": labels,
                            "scores": filtered_scores,
                            "combined_mask": combined_mask,
                            "image_shape": original_shape,
                        }
                    )

            except Exception as e:
                logger.error(
                    f"SAM 2 batch segmentation failed on batch {i//batch_size}: {e}"
                )
                # Append empty results as fallback
                for orig_size in original_sizes:
                    all_results.append(
                        {
                            "masks": [],
                            "labels": [],
                            "scores": [],
                            "combined_mask": np.zeros(orig_size, dtype=np.uint8),
                            "image_shape": orig_size,
                        }
                    )

        return all_results
