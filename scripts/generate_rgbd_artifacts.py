"""Generate RGBD artifacts from Nutrition5k raw data.

Processes each dish in the MVP subset:
1. Load overhead RGB image
2. Apply RGB preprocessing (bilateral filter + CLAHE)
3. Load 16-bit depth map (if available) or generate placeholder
4. Apply depth preprocessing (normalize to [0, 1])
5. Resize both to target_size with letterboxing
6. Stack into (4, H, W) RGBD tensor
7. Save as .npy to data/processed/rgbd/

Generates a manifest CSV recording each artifact.

Usage:
    python scripts/generate_rgbd_artifacts.py --config configs/data/data_config.yaml
    python scripts/generate_rgbd_artifacts.py --config configs/data/data_config.yaml --limit 10
"""
import argparse
import csv
import sys
from pathlib import Path

import cv2
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.preprocessing import (
    preprocess_rgb,
    preprocess_depth,
    resize_with_letterbox,
    load_preprocessing_config,
    normalize_for_model,
)
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_SIZE = (224, 224)


def find_dish_images(raw_dir: Path, dish_id: str) -> list[dict]:
    """Find multiple RGB/Depth views for a dish.
    
    Returns list of dicts: {"rgb": Path, "depth": Path | None, "view_id": str}
    """
    views = []
    
    # View 0: Overhead (Realsense)
    overhead_dir = raw_dir / "imagery" / "realsense_overhead" / dish_id
    rgb_overhead = overhead_dir / "rgb.png"
    if not rgb_overhead.exists():
        rgb_overhead = overhead_dir / "rgb.jpg"
        
    if rgb_overhead.exists():
        depth_overhead = overhead_dir / "depth_raw.png"
        views.append({
            "rgb": rgb_overhead,
            "depth": depth_overhead if depth_overhead.exists() else None,
            "view_id": "overhead"
        })

    # Side Views (A, B, C frames)
    side_dir = raw_dir / "imagery" / "side_angles" / dish_id
    if side_dir.exists():
        # Pick a few representative frames from different cameras
        for cam in ["A", "B", "C"]:
            # Pick frame 001 as a representative side view
            side_rgb = side_dir / f"camera_{cam}frame001.jpeg"
            if side_rgb.exists():
                views.append({
                    "rgb": side_rgb,
                    "depth": None, # Side angles usually don't have matching depth in this structure
                    "view_id": f"side_{cam.lower()}"
                })
                
    return views


def generate_rgbd(
    rgb_path: Path,
    depth_path: Path | None,
    preproc_config: dict,
    target_size: tuple[int, int] = TARGET_SIZE,
) -> np.ndarray:
    """Generate a single RGBD artifact.

    Args:
        rgb_path: Path to RGB image.
        depth_path: Path to 16-bit depth map (or None for placeholder).
        preproc_config: Preprocessing config dict.
        target_size: (H, W) output size.

    Returns:
        RGBD tensor as np.ndarray, shape (4, H, W), dtype float32.
    """
    # Load and preprocess RGB
    bgr = cv2.imread(str(rgb_path))
    if bgr is None:
        raise ValueError(f"Failed to read RGB image: {rgb_path}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    rgb = preprocess_rgb(rgb, config=preproc_config)
    rgb = resize_with_letterbox(rgb, target_size=target_size)
    rgb_norm = normalize_for_model(rgb)  # (H, W, 3) float32

    # Load and preprocess depth
    if depth_path is not None and depth_path.exists():
        depth_raw = cv2.imread(str(depth_path), cv2.IMREAD_UNCHANGED)
        if depth_raw is None:
            logger.warning(f"Failed to read depth, using placeholder: {depth_path}")
            depth_norm = np.zeros(target_size, dtype=np.float32)
        else:
            if depth_raw.ndim == 3:
                depth_raw = cv2.cvtColor(depth_raw, cv2.COLOR_BGR2GRAY)
            
            depth_norm = preprocess_depth(depth_raw.astype(np.uint16), config=preproc_config)
            depth_norm = resize_with_letterbox(
                depth_norm, target_size=target_size, fill_value=(0,)
            )
            if depth_norm.ndim == 3:
                depth_norm = depth_norm[:, :, 0]
    else:
        # No depth map found, using placeholder zeros
        depth_norm = np.zeros(target_size, dtype=np.float32)

    depth_norm = depth_norm.astype(np.float32)

    # Stack: (4, H, W) — channels first
    rgb_chw = np.transpose(rgb_norm, (2, 0, 1))  # (3, H, W)
    depth_chw = depth_norm[np.newaxis, :, :]       # (1, H, W)
    rgbd = np.concatenate([rgb_chw, depth_chw], axis=0)  # (4, H, W)

    return rgbd.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Generate RGBD artifacts from Nutrition5k")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--preproc-config", default="configs/data/preprocessing.yaml", help="Preprocessing config")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N dishes")
    parser.add_argument("--target-size", type=int, nargs=2, default=[224, 224], help="H W target size")
    args = parser.parse_args()

    # Load configs
    data_cfg = load_data_config(args.config)
    preproc_cfg = load_preprocessing_config(args.preproc_config)
    raw_dir = Path(data_cfg.raw_dir)
    output_dir = Path(data_cfg.processed_dir) / "rgbd"
    output_dir.mkdir(parents=True, exist_ok=True)
    target_size = tuple(args.target_size)

    # Load dish IDs from split files
    splits_dir = Path(data_cfg.splits_dir)
    dish_ids = []
    for split in ["train", "val", "test"]:
        split_file = splits_dir / f"{split}_ids.txt"
        if split_file.exists():
            dish_ids.extend([line.strip() for line in split_file.read_text().splitlines() if line.strip()])
    
    # Deduplicate while preserving order
    dish_ids = list(dict.fromkeys(dish_ids))

    if args.limit:
        dish_ids = dish_ids[:args.limit]

    logger.info(f"Processing {len(dish_ids)} dishes with multi-view support to {output_dir}")

    # Generate artifacts and manifest
    manifest_path = output_dir / "manifest.csv"
    stats = {"success": 0, "skipped": 0, "failed": 0}

    with open(manifest_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["dish_id", "view_id", "rgbd_path", "shape", "rgb_source", "depth_source"])

        for i, dish_id in enumerate(dish_ids):
            try:
                views = find_dish_images(raw_dir, dish_id)
                if not views:
                    logger.warning(f"[{i+1}/{len(dish_ids)}] Skipped {dish_id}: no images found")
                    stats["skipped"] += 1
                    continue

                for view in views:
                    view_id = view["view_id"]
                    try:
                        rgbd = generate_rgbd(view["rgb"], view["depth"], preproc_cfg, target_size)

                        # Save: <dish_id>_<view_id>.npy
                        out_path = output_dir / f"{dish_id}_{view_id}.npy"
                        np.save(str(out_path), rgbd)

                        # Record in manifest
                        try:
                            rel_path = out_path.relative_to(PROJECT_ROOT)
                        except ValueError:
                            rel_path = out_path

                        writer.writerow([
                            dish_id,
                            view_id,
                            str(rel_path),
                            f"({rgbd.shape[0]},{rgbd.shape[1]},{rgbd.shape[2]})",
                            str(view["rgb"]),
                            str(view["depth"]) if view["depth"] else "none",
                        ])
                        stats["success"] += 1
                    except Exception as ve:
                        logger.error(f"Failed view {view_id} for {dish_id}: {ve}")
                        stats["failed"] += 1

                if (i + 1) % 50 == 0 or (i + 1) == len(dish_ids):
                    logger.info(f"[{i+1}/{len(dish_ids)}] Processed {dish_id} (found {len(views)} views)")

            except Exception as e:
                logger.error(f"[{i+1}/{len(dish_ids)}] Major failure for {dish_id}: {e}")
                stats["failed"] += 1

    # Summary
    logger.info("=" * 60)
    logger.info(f"RGBD Artifact Generation Complete")
    logger.info(f"  Success: {stats['success']}")
    logger.info(f"  Skipped: {stats['skipped']} (no RGB found)")
    logger.info(f"  Failed:  {stats['failed']}")
    logger.info(f"  Output:  {output_dir}")
    logger.info(f"  Manifest: {manifest_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
