#!/usr/bin/env python3
"""Phase 3: Feature Assembly script.

Assembles preprocessed RGB, Depth, and Masks into final artifacts.
Saves stacked RGBD tensors as .npy in data/processed/rgbd/.
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import cv2

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger
from nutrisnap.data.preprocessing import resize_with_letterbox

logger = get_logger(__name__)

TARGET_SIZE = (224, 224)

def main():
    parser = argparse.ArgumentParser(description="Phase 3: Feature Assembly")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of dishes processed")
    args = parser.parse_args()

    # Load data config
    cfg = load_data_config(args.config)
    interim_dir = Path(cfg.interim_dir)
    processed_dir = Path(cfg.processed_dir)
    
    rgb_dir = interim_dir / "rgb"
    depth_dir = interim_dir / "depth"
    mask_dir = interim_dir / "masks"
    output_dir = processed_dir / "rgbd"
    output_dir.mkdir(parents=True, exist_ok=True)

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

    logger.info(f"Assembling features for {len(dish_ids)} dishes into {output_dir}")

    success_count = 0
    fail_count = 0
    
    manifest_path = output_dir / "manifest.csv"
    with open(manifest_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["dish_id", "view_id", "rgbd_path", "has_depth", "has_mask"])

        for i, dish_id in enumerate(dish_ids):
            # Find all RGB views for this dish in interim
            rgb_files = list(rgb_dir.glob(f"{dish_id}_*.npy"))
            if not rgb_files:
                continue

            for rgb_path in rgb_files:
                view_id = rgb_path.stem.replace(f"{dish_id}_", "")
                out_path = output_dir / f"{dish_id}_{view_id}.npy"

                try:
                    # Load RGB (H, W, 3)
                    rgb_norm = np.load(str(rgb_path))
                    
                    # Load Depth (H, W) if exists, else zeros
                    depth_path = depth_dir / f"{dish_id}_{view_id}.npy"
                    has_depth = False
                    if depth_path.exists():
                        depth_norm = np.load(str(depth_path))
                        has_depth = True
                    else:
                        depth_norm = np.zeros(TARGET_SIZE, dtype=np.float32)

                    # Load Mask (H, W) if exists
                    mask_path = mask_dir / f"{dish_id}_{view_id}.png"
                    has_mask = False
                    if mask_path.exists():
                        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
                        if mask is not None:
                            mask = resize_with_letterbox(mask, target_size=TARGET_SIZE, fill_value=(0,))
                            mask = (mask > 127).astype(np.float32)
                            has_mask = True
                        else:
                            mask = np.ones(TARGET_SIZE, dtype=np.float32) # Default to all if mask failed
                    else:
                        mask = np.ones(TARGET_SIZE, dtype=np.float32)

                    # For now, we follow the (4, H, W) format from the old script (RGB + Depth)
                    # We might want to include the mask as a 5th channel or apply it to RGB/Depth
                    # The old script was just RGBD.
                    
                    # Stack: (4, H, W)
                    rgb_chw = np.transpose(rgb_norm, (2, 0, 1))  # (3, H, W)
                    depth_chw = depth_norm[np.newaxis, :, :]       # (1, H, W)
                    rgbd = np.concatenate([rgb_chw, depth_chw], axis=0)
                    
                    # Optional: apply mask to RGBD? 
                    # If we have a mask, we can zero out non-food areas.
                    # rgbd *= mask[np.newaxis, :, :]

                    # Save
                    np.save(str(out_path), rgbd.astype(np.float32))
                    
                    writer.writerow([dish_id, view_id, str(out_path.relative_to(processed_dir.parent.parent)), has_depth, has_mask])
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to assemble {dish_id} ({view_id}): {e}")
                    fail_count += 1

    logger.info("=" * 60)
    logger.info("PHASE 3 COMPLETE: Features Assembled")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed:  {fail_count}")
    logger.info(f"  Output:  {output_dir}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
