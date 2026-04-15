#!/usr/bin/env python3
"""Phase 3: RGB Preprocessing script.

Applies bilateral filter and CLAHE to RGB images.
Saves preprocessed RGB as .npy in data/interim/rgb/.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.data.preprocessing import (
    preprocess_rgb,
    resize_with_letterbox,
    load_preprocessing_config,
    normalize_for_model,
)
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_SIZE = (224, 224)

def find_dish_images(raw_dir: Path, dish_id: str) -> list[dict]:
    """Find multiple RGB views for a dish."""
    views = []
    # View 0: Overhead (Realsense)
    overhead_dir = raw_dir / "imagery" / "realsense_overhead" / dish_id
    rgb_overhead = overhead_dir / "rgb.png"
    if not rgb_overhead.exists():
        rgb_overhead = overhead_dir / "rgb.jpg"
    if rgb_overhead.exists():
        views.append({"rgb": rgb_overhead, "view_id": "overhead"})
    
    # Side Views (A, B, C frames)
    side_dir = raw_dir / "imagery" / "side_angles" / dish_id
    if side_dir.exists():
        for cam in ["A", "B", "C"]:
            # Pick frame 001 as a representative side view
            side_rgb = side_dir / f"camera_{cam}frame001.jpeg"
            if side_rgb.exists():
                views.append({"rgb": side_rgb, "view_id": f"side_{cam.lower()}"})
    return views

def main():
    parser = argparse.ArgumentParser(description="Phase 3: RGB Preprocessing")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--preproc-config", default="configs/data/preprocessing.yaml", help="Preprocessing config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of dishes processed")
    args = parser.parse_args()

    # Load data config
    cfg = load_data_config(args.config)
    preproc_cfg = load_preprocessing_config(args.preproc_config)
    raw_dir = Path(cfg.raw_dir)
    rgb_dir = Path(cfg.interim_dir) / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)

    # Load dish IDs from split files
    splits_dir = Path(cfg.splits_dir)
    dish_ids = []
    for split in ["train", "val", "test"]:
        split_file = splits_dir / f"{split}_ids.txt"
        if split_file.exists():
            dish_ids.extend([line.strip() for line in split_file.read_text().splitlines() if line.strip()])
    
    # Deduplicate while preserving order
    dish_ids = list(dict.fromkeys(dish_ids))

    if args.limit:
        dish_ids = dish_ids[:args.limit]

    logger.info(f"Preprocessing RGB for {len(dish_ids)} dishes in {rgb_dir}")

    success_count = 0
    fail_count = 0

    for i, dish_id in enumerate(dish_ids):
        views = find_dish_images(raw_dir, dish_id)
        if not views:
            continue

        for view in views:
            view_id = view["view_id"]
            out_path = rgb_dir / f"{dish_id}_{view_id}.npy"
            
            # Skip if already exists
            if out_path.exists():
                success_count += 1
                continue

            try:
                # Load RGB
                bgr = cv2.imread(str(view["rgb"]))
                if bgr is None:
                    logger.warning(f"Failed to read RGB image: {view['rgb']}")
                    continue
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

                # Preprocess
                rgb = preprocess_rgb(rgb, config=preproc_cfg)
                rgb = resize_with_letterbox(rgb, target_size=TARGET_SIZE)
                rgb_norm = normalize_for_model(rgb)  # (H, W, 3) float32

                # Save
                np.save(str(out_path), rgb_norm)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to preprocess RGB {dish_id} ({view_id}): {e}")
                fail_count += 1

    logger.info("=" * 60)
    logger.info("PHASE 3 COMPLETE: RGB Preprocessed")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed:  {fail_count}")
    logger.info(f"  Output:  {rgb_dir}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
