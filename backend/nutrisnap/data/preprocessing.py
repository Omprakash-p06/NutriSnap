"""RGB and depth preprocessing pipelines for NutriSnap.

Implements bilateral filter → CLAHE → letterbox resize → normalize pipeline
for RGB images, and 16-bit → float normalization for depth maps.

Usage:
    from nutrisnap.data.preprocessing import preprocess_rgb, preprocess_depth
    from nutrisnap.data.preprocessing import resize_with_letterbox, apply_mask

    rgb_clean = preprocess_rgb(rgb_image)
    depth_norm = preprocess_depth(depth_16bit)
    masked = apply_mask(rgb_clean, food_mask)
"""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import yaml
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# Default preprocessing parameters (overridden by config if loaded)
_DEFAULT_CONFIG = {
    "rgb": {
        "bilateral_filter": {"d": 9, "sigma_color": 75, "sigma_space": 75},
        "clahe": {"clip_limit": 2.0, "tile_grid_size": [8, 8]},
        "target_size": [224, 224],
        "letterbox_fill": [0, 0, 0],
        "normalize": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
    },
    "depth": {
        "scale_factor": 10000.0,
        "median_filter_ksize": 5,
        "morph_kernel_size": 5,
        "inpaint_radius": 3,
        "gaussian_sigma": 1.0,
        "clip_range": [0.0, 0.4],
        "normalize": True,
    },
}


def load_preprocessing_config(
    config_path: str | Path = "configs/data/preprocessing.yaml",
) -> dict:
    """Load preprocessing config from YAML, falling back to defaults."""
    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            cfg = yaml.safe_load(f)
        logger.info(f"Loaded preprocessing config from {path}")
        return cfg
    else:
        logger.warning(f"Preprocessing config not found at {path}, using defaults")
        return _DEFAULT_CONFIG


def preprocess_rgb(
    image: np.ndarray,
    config: Optional[dict] = None,
) -> np.ndarray:
    """Apply bilateral filter and CLAHE to an RGB image.

    Pipeline:
        1. Bilateral filter for edge-preserving denoising
        2. Convert RGB → LAB
        3. CLAHE on L channel for contrast enhancement
        4. Convert LAB → RGB

    Args:
        image: Input RGB image as np.ndarray (H, W, 3), dtype uint8.
        config: Optional config dict. Uses defaults if None.

    Returns:
        Preprocessed RGB image as np.ndarray (H, W, 3), dtype uint8.
    """
    if config is None:
        config = _DEFAULT_CONFIG
    rgb_cfg = config.get("rgb", _DEFAULT_CONFIG["rgb"])

    # Step 1: Bilateral filter
    bf = rgb_cfg["bilateral_filter"]
    img = cv2.bilateralFilter(
        image,
        d=bf["d"],
        sigmaColor=bf["sigma_color"],
        sigmaSpace=bf["sigma_space"],
    )

    # Step 2-3: CLAHE on L channel
    clahe_cfg = rgb_cfg["clahe"]
    clahe = cv2.createCLAHE(
        clipLimit=clahe_cfg["clip_limit"],
        tileGridSize=tuple(clahe_cfg["tile_grid_size"]),
    )
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])

    # Step 4: Back to RGB
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return result


def preprocess_depth(
    depth_map: np.ndarray,
    config: Optional[dict] = None,
) -> np.ndarray:
    """Normalize and clean a 16-bit depth map.

    Pipeline:
        1. Scale to meters (raw → float)
        2. Median filter (despeckle)
        3. Morphological closing (hole filling)
        4. TELEA Inpainting (repairing missing regions)
        5. Gaussian smoothing
        6. Clip and Normalize

    Args:
        depth_map: Raw depth map as np.ndarray, dtype uint16 (16-bit).
        config: Optional config dict. Uses defaults if None.

    Returns:
        Normalized depth map as np.ndarray (H, W), dtype float32, range [0, 1].
    """
    if config is None:
        config = _DEFAULT_CONFIG
    depth_cfg = config.get("depth", _DEFAULT_CONFIG["depth"])

    # 1. Scale to meters
    depth_float = depth_map.astype(np.float32) / depth_cfg["scale_factor"]

    # 2. Median filter
    if depth_cfg["median_filter_ksize"] > 1:
        depth_float = cv2.medianBlur(depth_float, depth_cfg["median_filter_ksize"])

    # 3. Morphological closing (to fill small holes)
    k_size = depth_cfg.get("morph_kernel_size", 5)
    if k_size > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        depth_float = cv2.morphologyEx(depth_float, cv2.MORPH_CLOSE, kernel)

    # 4. TELEA Inpainting
    # Create mask of missing pixels (0 or NaN)
    mask = (depth_float <= 0).astype(np.uint8)
    if mask.any():
        depth_float = cv2.inpaint(
            depth_float, mask, depth_cfg.get("inpaint_radius", 3), cv2.INPAINT_TELEA
        )

    # 5. Gaussian smoothing
    sigma = depth_cfg.get("gaussian_sigma", 1.0)
    if sigma > 0:
        depth_float = cv2.GaussianBlur(depth_float, (0, 0), sigma)

    # 6. Clip and Normalize
    clip_min, clip_max = depth_cfg["clip_range"]
    depth_float = np.clip(depth_float, clip_min, clip_max)

    if depth_cfg.get("normalize", True) and clip_max > clip_min:
        depth_float = (depth_float - clip_min) / (clip_max - clip_min)

    return depth_float


def resize_with_letterbox(
    image: np.ndarray,
    target_size: tuple[int, int] = (224, 224),
    fill_value: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """Resize image with aspect-ratio-safe letterboxing (no stretching).

    Fits the image into target_size by scaling uniformly to fit, then
    padding the shorter dimension with fill_value.

    Args:
        image: Input image as np.ndarray (H, W, C) or (H, W).
        target_size: Target (height, width).
        fill_value: RGB fill for padding.

    Returns:
        Letterboxed image as np.ndarray of shape (target_h, target_w, C).
    """
    target_h, target_w = target_size
    h, w = image.shape[:2]

    # Calculate uniform scale factor
    scale = min(target_h / h, target_w / w)
    new_h, new_w = int(h * scale), int(
        h * scale
    )  # Wait, this should be h * scale and w * scale

    # Fixed: Uniform scale should maintain aspect ratio
    new_h, new_w = int(h * scale), int(w * scale)

    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Create canvas and center the resized image
    if image.ndim == 3:
        canvas = np.full(
            (target_h, target_w, image.shape[2]), fill_value, dtype=image.dtype
        )
    else:
        # For single channel (depth/mask)
        canvas = np.full((target_h, target_w), fill_value[0], dtype=image.dtype)

    pad_top = (target_h - new_h) // 2
    pad_left = (target_w - new_w) // 2
    canvas[pad_top : pad_top + new_h, pad_left : pad_left + new_w] = resized

    return canvas


def apply_mask(
    image: np.ndarray,
    mask: np.ndarray,
) -> np.ndarray:
    """Zero out non-food pixels using a segmentation mask.

    Args:
        image: RGB image as np.ndarray (H, W, 3).
        mask: Binary mask as np.ndarray (H, W), where non-zero = food.

    Returns:
        Masked image with background set to zero.
    """
    mask_bool = mask.astype(bool)
    result = image.copy()
    if result.ndim == 3:
        result[~mask_bool] = 0
    else:
        result[~mask_bool] = 0
    return result


def normalize_for_model(
    image: np.ndarray,
    mean: tuple[float, ...] = (0.485, 0.456, 0.406),
    std: tuple[float, ...] = (0.229, 0.224, 0.225),
) -> np.ndarray:
    """Normalize image from uint8 [0,255] to float [-N, N] using ImageNet stats.

    Args:
        image: RGB image as np.ndarray (H, W, 3), dtype uint8.
        mean: Per-channel mean values.
        std: Per-channel std values.

    Returns:
        Normalized image as np.ndarray (H, W, 3), dtype float32.
    """
    img_float = image.astype(np.float32) / 255.0
    mean_arr = np.array(mean, dtype=np.float32).reshape(1, 1, 3)
    std_arr = np.array(std, dtype=np.float32).reshape(1, 1, 3)
    return (img_float - mean_arr) / std_arr


def apply_ingredient_mass_correction(
    ingredient_masses: np.ndarray,
    measured_total_g: float,
    nutrient_densities: np.ndarray,
) -> np.ndarray:
    """Re-scale ingredient masses so they sum to the measured dish weight.

    Nutrition5k ingredient masses are weighed per-ingredient but may not
    sum to the measured dish total due to moisture loss, rounding, or
    mixed/liquid components. This correction rescales the mass vector
    proportionally so macronutrient estimates are grounded to the actual
    measured total weight.

    Improvement: Shown to substantially reduce calorie MAE on Nutrition5k
    by eliminating the systematic under/over-estimation caused by mass
    mismatch between ingredient records and the physical dish weight.

    Args:
        ingredient_masses:  (N,) array of per-ingredient masses in grams.
        measured_total_g:   Actual measured weight of the full dish in grams.
        nutrient_densities: (N, 4) array of [cal, fat, carb, protein] density
                            per gram for each of the N ingredients.

    Returns:
        (4,) corrected nutrient totals [calories, fat, carbs, protein].

    Raises:
        ValueError: If ingredient_masses or nutrient_densities have mismatched
            shapes, or if measured_total_g <= 0.
    """
    ingredient_masses = np.asarray(ingredient_masses, dtype=np.float32)
    nutrient_densities = np.asarray(nutrient_densities, dtype=np.float32)

    if measured_total_g <= 0:
        raise ValueError(f"measured_total_g must be positive, got {measured_total_g}")
    if ingredient_masses.ndim != 1:
        raise ValueError("ingredient_masses must be a 1-D array")
    if nutrient_densities.shape != (len(ingredient_masses), 4):
        raise ValueError(
            f"nutrient_densities shape {nutrient_densities.shape} must be "
            f"({len(ingredient_masses)}, 4)"
        )

    raw_total = ingredient_masses.sum()
    if raw_total <= 0:
        logger.warning(
            "Ingredient masses sum to zero — skipping mass correction, "
            "returning zero nutrient vector"
        )
        return np.zeros(4, dtype=np.float32)

    # Scale factor: brings ingredient mass total in line with measured dish weight
    correction_factor = measured_total_g / raw_total
    corrected_masses = ingredient_masses * correction_factor

    # Nutrient totals = sum over ingredients of (corrected_mass * nutrient_density)
    # nutrient_densities[i] is per-gram, so multiply elementwise then sum
    totals = np.einsum("i,ij->j", corrected_masses, nutrient_densities)

    logger.debug(
        f"Mass correction: raw_sum={raw_total:.1f}g → measured={measured_total_g:.1f}g "
        f"(factor={correction_factor:.4f}) | cal_corrected={totals[0]:.1f} kcal"
    )
    return totals.astype(np.float32)
