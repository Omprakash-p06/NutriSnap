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
from concurrent.futures import ProcessPoolExecutor, as_completed
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


def process_dish_task(dish_id, imagery_dir, side_dir, output_dir, sampling_rate=1, max_frames=None):
    """Worker task for all views of a single dish."""
    results = {"overhead": 0, "side": 0, "failed": 0}

    # 1. Overhead View (RGB + Depth)
    dish_overhead_dir = imagery_dir / dish_id
    if dish_overhead_dir.exists():
        rgb_out = output_dir / f"{dish_id}_overhead_rgb.pt"
        depth_out = output_dir / f"{dish_id}_overhead_depth.pt"

        if not (rgb_out.exists() and depth_out.exists()):
            rgb_path = dish_overhead_dir / "rgb.png"
            depth_path = dish_overhead_dir / "depth_raw.png"
            rgb_t = preprocess_rgb(rgb_path)
            if rgb_t is not None:
                depth_t = preprocess_depth(depth_path)
                torch.save(rgb_t, rgb_out)
                torch.save(depth_t, depth_out)
                results["overhead"] += 1
            else:
                results["failed"] += 1

    # 2. Side Angle Views (RGB only, sampled)
    dish_side_dir = side_dir / dish_id
    if dish_side_dir.exists():
        all_frames = sorted(list(dish_side_dir.glob("*.jpeg")) + list(dish_side_dir.glob("*.jpg")))
        
        # Apply sampling rate
        sampled_frames = all_frames[::sampling_rate]
        
        # Apply max frames limit if specified
        if max_frames and len(sampled_frames) > max_frames:
            # Take a uniform sample if exceeding max_frames
            indices = np.linspace(0, len(sampled_frames) - 1, max_frames, dtype=int)
            sampled_frames = [sampled_frames[i] for i in indices]

        for frame_path in sampled_frames:
            name = frame_path.stem
            rgb_out = output_dir / f"{dish_id}_{name}_rgb.pt"
            depth_out = output_dir / f"{dish_id}_{name}_depth.pt"

            if rgb_out.exists() and depth_out.exists():
                results["side"] += 1
                continue

            rgb_t = preprocess_rgb(frame_path)
            if rgb_t is not None:
                depth_t = torch.zeros((1, IMAGE_SIZE[1], IMAGE_SIZE[0]), dtype=torch.float32)
                torch.save(rgb_t, rgb_out)
                torch.save(depth_t, depth_out)
                results["side"] += 1
            else:
                results["failed"] += 1

    return results


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
    parser.add_argument("--workers", type=int, default=4, help="Number of CPU workers")
    parser.add_argument("--sampling-rate", type=int, default=1, help="Sample every Nth frame")
    parser.add_argument("--max-frames", type=int, default=None, help="Max frames per dish")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = Path(cfg["data"]["raw_path"])
    imagery_dir = raw_path / cfg["data"]["imagery_subdir"]
    side_dir = raw_path / "imagery" / "side_angles"

    dish_ids = get_dish_ids(args, cfg)
    logger.info(
        f"Processing {len(dish_ids)} dishes using {args.workers} workers (Multi-View) -> {output_dir}"
    )

    overhead_count = 0
    side_count = 0
    failed_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_dish_task, dish_id, imagery_dir, side_dir, output_dir, 
                sampling_rate=args.sampling_rate, max_frames=args.max_frames
            ): dish_id
            for dish_id in dish_ids
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="DIP Multi-View"):
            res = future.result()
            overhead_count += res["overhead"]
            side_count += res["side"]
            failed_count += res["failed"]

    # Optional: Run SAM sequentially after DIP if masking is requested
    # Note: For 4,000 images, this might take > 1 hour.
    if not args.no_segment:
        logger.info("Starting sequential SAM masking pass (this will iterate all generated .pt files)...")
        segment_cfg = cfg.get("segmentation_config", "configs/pipeline/segmenter.yaml")
        try:
            segmenter = FoodSegmenter(config_path=segment_cfg)
            all_tensors = list(output_dir.glob("*_rgb.pt"))
            for rgb_out in tqdm(all_tensors, desc="SAM Masking"):
                depth_out = Path(str(rgb_out).replace("_rgb.pt", "_depth.pt"))
                if not depth_out.exists():
                    continue

                # We need the original image for SAM.
                # Naming convention: {dish_id}_{view/camframe}_rgb.pt
                # We can't easily map back to the JPEG unless we store the path OR re-search.
                # Simplified strategy: skip SAM for side-angles in MVP if complexity is too high, 
                # OR assume naming helps.
                
                # Logic to find source image:
                stem = rgb_out.stem  # e.g. dish_1550704750_camera_Aframe001_rgb
                dish_id = "_".join(stem.split("_")[:2])
                frame_info = "_".join(stem.split("_")[2:-1]) # e.g. camera_Aframe001
                
                if frame_info == "overhead":
                    src_path = imagery_dir / dish_id / "rgb.png"
                else:
                    src_path = side_dir / dish_id / f"{frame_info}.jpeg"

                if not src_path.exists():
                    src_path = side_dir / dish_id / f"{frame_info}.jpg"

                if not src_path.exists():
                    continue

                rgb_tensor = torch.load(rgb_out)
                depth_tensor = torch.load(depth_out)

                seg_result = segmenter.segment(src_path)
                mask = seg_result["combined_mask"] / 255.0
                mask_tensor = torch.from_numpy(mask).float().unsqueeze(0)
                mask_tensor = T.Resize(
                    (224, 224), interpolation=T.InterpolationMode.NEAREST
                )(mask_tensor)

                rgb_tensor = rgb_tensor * mask_tensor
                depth_tensor = depth_tensor * mask_tensor

                torch.save(rgb_tensor, rgb_out)
                torch.save(depth_tensor, depth_out)
                segmenter.unload()
        except Exception as e:
            logger.error(f"SAM Sequential pass failed: {e}")

    logger.info(
        f"Done — overhead: {overhead_count} | side frames: {side_count} | failed: {failed_count}"
    )
    logger.info(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
