#!/usr/bin/env python3
"""Phase 2: Segmentation script.

Generates food masks for the Nutrition5k dataset.
Saves masks as PNG files in data/interim/masks/.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.pipeline.segmenter import FoodSegmenter
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

def find_dish_images(raw_dir: Path, dish_id: str) -> list[dict]:
    """Find multiple RGB views for a dish.
    
    Returns list of dicts: {"rgb": Path, "view_id": str}
    """
    views = []
    
    # View 0: Overhead (Realsense)
    overhead_dir = raw_dir / "imagery" / "realsense_overhead" / dish_id
    rgb_overhead = overhead_dir / "rgb.png"
    if not rgb_overhead.exists():
        rgb_overhead = overhead_dir / "rgb.jpg"
        
    if rgb_overhead.exists():
        views.append({
            "rgb": rgb_overhead,
            "view_id": "overhead"
        })

    # Side Views (A, B, C frames)
    side_dir = raw_dir / "imagery" / "side_angles" / dish_id
    if side_dir.exists():
        for cam in ["A", "B", "C"]:
            # Pick frame 001 as a representative side view
            side_rgb = side_dir / f"camera_{cam}frame001.jpeg"
            if side_rgb.exists():
                views.append({
                    "rgb": side_rgb,
                    "view_id": f"side_{cam.lower()}"
                })
                
    return views

def main():
    parser = argparse.ArgumentParser(description="Phase 2: Generate Food Masks")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of dishes processed")
    args = parser.parse_args()

    # Load data config
    cfg = load_data_config(args.config)
    raw_dir = Path(cfg.raw_dir)
    interim_dir = Path(cfg.interim_dir)
    mask_dir = interim_dir / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)

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

    logger.info(f"Generating masks for {len(dish_ids)} dishes in {mask_dir}")

    # Initialize segmenter
    try:
        segmenter = FoodSegmenter()
    except Exception as e:
        logger.error(f"Failed to initialize segmenter: {e}")
        sys.exit(1)

    success_count = 0
    fail_count = 0

    for i, dish_id in enumerate(dish_ids):
        views = find_dish_images(raw_dir, dish_id)
        if not views:
            continue

        for view in views:
            view_id = view["view_id"]
            out_path = mask_dir / f"{dish_id}_{view_id}.png"
            
            # Skip if already exists
            if out_path.exists():
                success_count += 1
                continue

            try:
                logger.info(f"[{i+1}/{len(dish_ids)}] Segmenting {dish_id} ({view_id})")
                result = segmenter.segment(view["rgb"])
                
                # result["combined_mask"] is (H, W) uint8 0/255
                cv2.imwrite(str(out_path), result["combined_mask"])
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to segment {dish_id} ({view_id}): {e}")
                fail_count += 1

    # Cleanup segmenter (VRAM)
    segmenter.unload()

    logger.info("=" * 60)
    logger.info("PHASE 2 COMPLETE: Food Masks Generated")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed:  {fail_count}")
    logger.info(f"  Output:  {mask_dir}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
