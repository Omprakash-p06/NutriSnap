#!/usr/bin/env python3
"""Phase 3: Depth Preprocessing script.

Normalizes depth maps and resizes them to target size.
Saves preprocessed depth as .npy in data/interim/depth/.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.data.preprocessing import (
    preprocess_depth,
    resize_with_letterbox,
    load_preprocessing_config,
)
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_SIZE = (224, 224)

def find_dish_depth(raw_dir: Path, dish_id: str) -> list[dict]:
    """Find depth views for a dish."""
    views = []
    # View 0: Overhead (Realsense)
    overhead_dir = raw_dir / "imagery" / "realsense_overhead" / dish_id
    depth_overhead = overhead_dir / "depth_raw.png"
    if depth_overhead.exists():
        views.append({"depth": depth_overhead, "view_id": "overhead"})
    
    # Side views usually don't have depth maps in Nutrition5k
    return views

def main():
    parser = argparse.ArgumentParser(description="Phase 3: Depth Preprocessing")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--preproc-config", default="configs/data/preprocessing.yaml", help="Preprocessing config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of dishes processed")
    args = parser.parse_args()

    # Load data config
    cfg = load_data_config(args.config)
    preproc_cfg = load_preprocessing_config(args.preproc_config)
    raw_dir = Path(cfg.raw_dir)
    depth_dir = Path(cfg.interim_dir) / "depth"
    depth_dir.mkdir(parents=True, exist_ok=True)

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

    logger.info(f"Preprocessing Depth for {len(dish_ids)} dishes in {depth_dir}")

    success_count = 0
    fail_count = 0

    for i, dish_id in enumerate(dish_ids):
        views = find_dish_depth(raw_dir, dish_id)
        
        # If no depth, we don't save anything in interim/depth
        if not views:
            continue

        for view in views:
            view_id = view["view_id"]
            out_path = depth_dir / f"{dish_id}_{view_id}.npy"
            
            # Skip if already exists
            if out_path.exists():
                success_count += 1
                continue

            try:
                # Load depth
                depth_raw = cv2.imread(str(view["depth"]), cv2.IMREAD_UNCHANGED)
                if depth_raw is None:
                    logger.warning(f"Failed to read depth image: {view['depth']}")
                    continue

                if depth_raw.ndim == 3:
                    depth_raw = cv2.cvtColor(depth_raw, cv2.COLOR_BGR2GRAY)

                # Preprocess
                depth_norm = preprocess_depth(depth_raw.astype(np.uint16), config=preproc_cfg)
                depth_norm = resize_with_letterbox(
                    depth_norm, target_size=TARGET_SIZE, fill_value=(0,)
                )
                if depth_norm.ndim == 3:
                    depth_norm = depth_norm[:, :, 0]

                # Save
                np.save(str(out_path), depth_norm.astype(np.float32))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to preprocess Depth {dish_id} ({view_id}): {e}")
                fail_count += 1

    logger.info("=" * 60)
    logger.info("PHASE 3 COMPLETE: Depth Preprocessed")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed:  {fail_count}")
    logger.info(f"  Output:  {depth_dir}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
