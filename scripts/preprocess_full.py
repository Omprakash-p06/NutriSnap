#!/usr/bin/env python3
"""Full preprocessing pipeline for Nutrition5k dataset.

Processes all dishes through the complete preprocessing chain:
  RGB:   Resize → Bilateral Filter → CLAHE → ImageNet Normalize → save _rgb.pt
  Depth: Scale (/10000) → Median Filter → TELEA Inpainting → Gaussian Smooth → Normalize → save _depth.pt

Resumable: skips dishes that already have both output files.

Usage:
    python scripts/preprocess_full.py [--config configs/data/data_config.yaml] [--ids-file datasets/splits/train_ids.txt]
    python scripts/preprocess_full.py --dish-id dish_1561662216  # single dish
"""

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision.transforms as T
import yaml
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.pipeline.depth import DepthEstimatorGLPN
from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2
from nutrisnap.utils.composite import create_composite_image
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


def process_dish_batch_3stage(dish_id, frame_paths, out_paths):
    """Process all frames for a dish using sequential stage execution to save VRAM."""
    # Filter out paths that already exist
    pending_indices = []
    for idx, op in enumerate(out_paths):
        if not op.exists():
            pending_indices.append(idx)

    if not pending_indices:
        return 0

    pending_frames = [frame_paths[i] for i in pending_indices]
    pending_outs = [out_paths[i] for i in pending_indices]

    logger.info(f"Processing {len(pending_frames)} frames for dish {dish_id}")

    batch_size = 4  # Reduced batch size for 4GB VRAM

    # 1. Stage 1: Depth Estimation (First Pass)
    depth_estimator = DepthEstimatorGLPN()
    all_depth_maps = []
    for i in range(0, len(pending_frames), batch_size):
        batch_frames = pending_frames[i : i + batch_size]
        depth_maps = depth_estimator.estimate_batch(batch_frames, batch_size=batch_size)
        all_depth_maps.extend(depth_maps)
    depth_estimator.unload()
    del depth_estimator

    # 2. Stage 2: Food Segmentation (Second Pass)
    segmenter = FoodSegmenterSAM2()
    all_seg_results = []
    for i in range(0, len(pending_frames), batch_size):
        batch_frames = pending_frames[i : i + batch_size]
        seg_results = segmenter.segment_batch(batch_frames, batch_size=batch_size)
        all_seg_results.extend(seg_results)
    segmenter.unload()
    del segmenter

    # 3. Stage 3: Create Composites
    count = 0
    for img_path, out_path, depth_map, seg_result in zip(
        pending_frames, pending_outs, all_depth_maps, all_seg_results
    ):
        # RGB Preprocessing
        rgb_tensor = preprocess_rgb(img_path)
        if rgb_tensor is None:
            continue

        # Depth Tensor
        depth_tensor = torch.from_numpy(depth_map).unsqueeze(0)
        depth_tensor = T.Resize(
            IMAGE_SIZE, interpolation=T.InterpolationMode.BILINEAR, antialias=True
        )(depth_tensor)

        # Mask Tensor
        mask = seg_result["combined_mask"] / 255.0
        mask_tensor = torch.from_numpy(mask).float().unsqueeze(0)
        mask_tensor = T.Resize(
            IMAGE_SIZE, interpolation=T.InterpolationMode.NEAREST, antialias=True
        )(mask_tensor)

        # Composite
        composite = create_composite_image(rgb_tensor, mask_tensor, depth_tensor)
        torch.save(composite, out_path)
        count += 1

    return count


def get_dish_ids(args, cfg: dict) -> list[str]:
    """Resolve which dish IDs to process."""
    if args.dish_id:
        return [args.dish_id]

    if args.mvp_only:
        mvp_file = Path(cfg.get("splits_dir", "datasets/splits")) / "mvp_subset_ids.txt"
        if mvp_file.exists():
            return [l.strip() for l in mvp_file.read_text().splitlines() if l.strip()]
        else:
            # Fallback to selected_dishes.json
            selected_file = Path("configs/data/selected_dishes.json")
            if selected_file.exists():
                import json

                with open(selected_file) as f:
                    return json.load(f)["dish_ids"]
            logger.error("MVP subset file and selected_dishes.json not found")
            sys.exit(1)

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


def process_dish_task(
    dish_id, imagery_dir, side_dir, output_dir, sampling_rate=1, max_frames=None
):
    """Worker task for all views of a single dish (Deprecated for 3-stage)."""
    pass  # Replaced by batching


def main():
    parser = argparse.ArgumentParser(
        description="NutriSnap Full Preprocessing Pipeline"
    )
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    parser.add_argument(
        "--ids-file", default=None, help="Text file with dish IDs to process"
    )
    parser.add_argument("--dish-id", default=None, help="Process a single dish ID")
    parser.add_argument(
        "--mvp-only",
        action="store_true",
        help="Process only the 10-dish MVP subset using SAM 2 + GLPN",
    )
    parser.add_argument("--output-dir", default="datasets/processed/features")
    parser.add_argument(
        "--no-segment",
        action="store_true",
        help="Skip SAM segmentation (background masking)",
    )
    parser.add_argument("--workers", type=int, default=4, help="Number of CPU workers")
    parser.add_argument(
        "--sampling-rate", type=int, default=1, help="Sample every Nth frame"
    )
    parser.add_argument(
        "--max-frames", type=int, default=None, help="Max frames per dish"
    )
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = Path(cfg["data"]["raw_path"])
    imagery_dir = raw_path / cfg["data"]["imagery_subdir"]
    side_dir = raw_path / "imagery" / "side_angles"

    dish_ids = get_dish_ids(args, cfg)

    if not args.no_segment:
        logger.info(
            f"Processing {len(dish_ids)} dishes using 3-stage pipeline (SAM 2 + GLPN) -> {output_dir}"
        )
        # Models are now managed per-dish in process_dish_batch_3stage to save VRAM

        composite_count = 0
        for dish_id in tqdm(dish_ids, desc="Processing Dishes (Batched)"):
            dish_frames = []
            dish_outs = []

            # Overhead
            overhead_img = imagery_dir / dish_id / "rgb.png"
            if overhead_img.exists():
                out_path = output_dir / f"{dish_id}_overhead_composite.pt"
                dish_frames.append(overhead_img)
                dish_outs.append(out_path)

            # Side Views
            dish_side_dir = side_dir / dish_id
            if dish_side_dir.exists():
                all_frames = sorted(
                    list(dish_side_dir.glob("*.jpeg"))
                    + list(dish_side_dir.glob("*.jpg"))
                )
                sampled_frames = all_frames[:: args.sampling_rate]
                if args.max_frames and len(sampled_frames) > args.max_frames:
                    indices = np.linspace(
                        0, len(sampled_frames) - 1, args.max_frames, dtype=int
                    )
                    sampled_frames = [sampled_frames[i] for i in indices]

                for frame_path in sampled_frames:
                    name = frame_path.stem
                    out_path = output_dir / f"{dish_id}_{name}_composite.pt"
                    dish_frames.append(frame_path)
                    dish_outs.append(out_path)

            if dish_frames:
                count = process_dish_batch_3stage(dish_id, dish_frames, dish_outs)
                composite_count += count
                # Also count files that already existed
                composite_count += len(dish_frames) - count

            # VRAM management
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        logger.info(
            f"Done 3-stage pipeline — verified/generated {composite_count} composite tensors."
        )
        return

    # Fallback to DIP-only parallel processing
    logger.info(
        f"Processing {len(dish_ids)} dishes using {args.workers} workers (DIP only) -> {output_dir}"
    )

    overhead_count = 0
    side_count = 0
    failed_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_dish_task,
                dish_id,
                imagery_dir,
                side_dir,
                output_dir,
                sampling_rate=args.sampling_rate,
                max_frames=args.max_frames,
            ): dish_id
            for dish_id in dish_ids
        }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="DIP Multi-View"
        ):
            res = future.result()
            overhead_count += res["overhead"]
            side_count += res["side"]
            failed_count += res["failed"]

    logger.info(
        f"Done — overhead: {overhead_count} | side frames: {side_count} | failed: {failed_count}"
    )
    logger.info(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
