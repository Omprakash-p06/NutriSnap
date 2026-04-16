#!/usr/bin/env python3
"""Full preprocessing pipeline for Nutrition5k dataset.

Processes all dishes through the complete preprocessing chain:
  RGB:   Resize → Bilateral Filter → CLAHE → ImageNet Normalize → save _rgb.pt
  Depth: Scale (/10000) → Median Filter → TELEA Inpainting → Gaussian Smooth → Normalize → save _depth.pt

Resumable: skips dishes that already have both output files.

Usage:
    python scripts/preprocess_full.py [--config configs/data/data_config.yaml] [--ids-file data/splits/train_ids.txt]
    python scripts/preprocess_full.py --dish-id dish_1561662216  # single dish
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms as T
import yaml
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.pipeline.segmenter import FoodSegmenter
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# ImageNet stats
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

IMAGE_SIZE = (224, 224)  # (W, H)


# ---------------------------------------------------------------------------
# RGB preprocessing
# ---------------------------------------------------------------------------


def preprocess_rgb(img_path: Path) -> torch.Tensor | None:
    """Full RGB pipeline → (3, 224, 224) float32 tensor."""
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    # BGR → RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 1. Resize to 224×224
    img = cv2.resize(img, IMAGE_SIZE, interpolation=cv2.INTER_AREA)

    # 2. Bilateral filter (edge-preserving noise reduction)
    img = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

    # 3. CLAHE on L-channel in LAB space (contrast enhancement)
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # 4. ImageNet normalize
    img = img.astype(np.float32) / 255.0
    img = (img - IMAGENET_MEAN) / IMAGENET_STD

    # 5. HWC → CHW
    img = img.transpose(2, 0, 1)
    return torch.from_numpy(img)


# ---------------------------------------------------------------------------
# Depth preprocessing
# ---------------------------------------------------------------------------


def preprocess_depth(depth_path: Path) -> torch.Tensor:
    """Full depth pipeline → (1, 224, 224) float32 tensor.

    Uses a zero-depth map if file is missing (graceful fallback).
    """
    if not depth_path.exists():
        logger.debug(f"Depth not found: {depth_path} — using zeros")
        return torch.zeros((1, IMAGE_SIZE[1], IMAGE_SIZE[0]), dtype=torch.float32)

    # Read 16-bit depth
    depth = cv2.imread(str(depth_path), cv2.IMREAD_UNCHANGED)
    if depth is None:
        return torch.zeros((1, IMAGE_SIZE[1], IMAGE_SIZE[0]), dtype=torch.float32)

    # 1. Convert from depth units (10,000 = 1 meter) to metres
    depth = depth.astype(np.float32) / 10_000.0

    # 2. Median filter (3×3) — removes salt-and-pepper noise
    depth = cv2.medianBlur(depth, 3)

    # 3. TELEA inpainting to fill missing/zero pixels
    mask = (depth == 0).astype(np.uint8) * 255
    if mask.any():
        # inpaint needs 8-bit image scaled to visible range
        depth_8u = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_8u = cv2.inpaint(depth_8u, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        # Scale back to float metres — preserve relative structure
        depth_filled_ratio = depth_8u.astype(np.float32) / 255.0
        max_depth = depth.max() if depth.max() > 0 else 1.0
        depth = depth_filled_ratio * max_depth

    # 4. Gaussian smoothing
    depth = cv2.GaussianBlur(depth, (5, 5), sigmaX=1.0)

    # 5. Resize to 224×224
    depth = cv2.resize(depth, IMAGE_SIZE, interpolation=cv2.INTER_NEAREST)

    # 6. Min-max normalize to [0, 1]
    d_min, d_max = depth.min(), depth.max()
    if d_max > d_min:
        depth = (depth - d_min) / (d_max - d_min)
    else:
        depth = np.zeros_like(depth)

    # CHW
    depth = depth[np.newaxis, :, :]  # (1, H, W)
    return torch.from_numpy(depth)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def get_dish_ids(args, cfg: dict) -> list[str]:
    """Resolve which dish IDs to process."""
    if args.dish_id:
        return [args.dish_id]

    if args.ids_file:
        ids_path = Path(args.ids_file)
        if not ids_path.exists():
            logger.error(f"IDs file not found: {ids_path}")
            sys.exit(1)
        return [l.strip() for l in ids_path.read_text().splitlines() if l.strip()]

    # Default: all dishes found in imagery dir
    raw_path = Path(cfg["data"]["raw_path"])
    imagery_dir = raw_path / cfg["data"]["imagery_subdir"]
    if not imagery_dir.exists():
        logger.error(f"Imagery directory not found: {imagery_dir}")
        sys.exit(1)
    return sorted([d.name for d in imagery_dir.iterdir() if d.is_dir()])


def main():
    parser = argparse.ArgumentParser(
        description="NutriSnap Full Preprocessing Pipeline"
    )
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    parser.add_argument(
        "--ids-file", default=None, help="Text file with dish IDs to process"
    )
    parser.add_argument("--dish-id", default=None, help="Process a single dish ID")
    parser.add_argument("--output-dir", default="data/processed/features")
    parser.add_argument(
        "--no-segment",
        action="store_true",
        help="Skip SAM segmentation (background masking)",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = Path(cfg["data"]["raw_path"])
    imagery_dir = raw_path / cfg["data"]["imagery_subdir"]

    dish_ids = get_dish_ids(args, cfg)
    logger.info(f"Processing {len(dish_ids)} dishes → {output_dir}")

    # Initialize segmenter (Phase 2.3)
    segmenter = None
    if not args.no_segment:
        try:
            segment_cfg = Path("configs/pipeline/segmenter.yaml")
            segmenter = FoodSegmenter(config_path=segment_cfg)
            logger.info("FoodSegmenter initialized for background masking.")
        except Exception as e:
            logger.error(
                f"Failed to initialize FoodSegmenter: {e}. Proceeding without masking."
            )
            segmenter = None

    skipped = 0
    failed = 0
    processed = 0

    for dish_id in tqdm(dish_ids, desc="Preprocessing"):
        rgb_out = output_dir / f"{dish_id}_rgb.pt"
        depth_out = output_dir / f"{dish_id}_depth.pt"

        # Resumable: skip if both already exist
        if rgb_out.exists() and depth_out.exists():
            skipped += 1
            continue

        dish_dir = imagery_dir / dish_id
        rgb_path = dish_dir / "rgb.png"
        depth_path = dish_dir / "depth_raw.png"

        rgb_tensor = preprocess_rgb(rgb_path)
        if rgb_tensor is None:
            logger.warning(f"[SKIP] No RGB for {dish_id}")
            failed += 1
            continue

        depth_tensor = preprocess_depth(depth_path)

        # Phase 2.3: SAM Masking
        if segmenter:
            try:
                # Run segmenter on raw RGB image
                # (Note: we use the raw image for SAM because it handles internal sizing)
                seg_result = segmenter.segment(rgb_path)

                # combined_mask is (H, W) uint8
                mask = seg_result["combined_mask"] / 255.0
                mask_tensor = torch.from_numpy(mask).float()

                # Resize mask to 224x224 to match tensors
                mask_tensor = T.Resize(
                    (224, 224), interpolation=T.InterpolationMode.NEAREST
                )(mask_tensor.unsqueeze(0))

                # Apply mask (broadcast across color channels)
                rgb_tensor = rgb_tensor * mask_tensor
                depth_tensor = depth_tensor * mask_tensor

                logger.debug(f"  [SEG] Mask applied to {dish_id}")
            except Exception as e:
                logger.warning(f"  [WARN] Segmentation failed for {dish_id}: {e}")
            finally:
                # Force VRAM cleanup after each dish
                segmenter.unload()

        torch.save(rgb_tensor, rgb_out)
        torch.save(depth_tensor, depth_out)
        processed += 1

    logger.info(
        f"Done — processed: {processed} | skipped (already exist): {skipped} | failed: {failed}"
    )
    logger.info(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
