"""Generate volume and area features for all processed artifacts.

This script loops through the RGBD artifacts manifest, performs segmentation
(if not already masked), and estimates volume/area using the VolumeEstimator.
Results are saved to a features CSV for downstream training.

Usage:
    python scripts/generate_volume_features.py --config configs/data/data_config.yaml
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import torch

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.pipeline.segmenter import FoodSegmenter
from nutrisnap.pipeline.volume import VolumeEstimator
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Generate volume features for Nutrition5k")
    parser.add_argument("--config", default="configs/data/data_config.yaml", help="Data config")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N dishes")
    args = parser.parse_args()

    # Load data config
    data_cfg = load_data_config(args.config)
    processed_dir = Path(data_cfg.processed_dir)
    rgbd_dir = processed_dir / "rgbd"
    manifest_path = rgbd_dir / "manifest.csv"

    if not manifest_path.exists():
        logger.error(f"RGBD manifest not found: {manifest_path}")
        sys.exit(1)

    # Output setup
    features_dir = processed_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    out_csv_path = features_dir / "volume_features.csv"

    # Initialize components
    # We load segmenter and estimator
    # NOTE: FoodSegmenter is heavy, VolumeEstimator is light.
    segmenter = FoodSegmenter()
    estimator = VolumeEstimator()

    # Load manifest
    with open(manifest_path, "r") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    if args.limit:
        records = records[:args.limit]

    logger.info(f"Generating volume features for {len(records)} artifacts...")

    results = []
    stats = {"success": 0, "failed": 0, "total_time": 0.0}

    with open(out_csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["dish_id", "volume_cm3", "area_cm2", "confidence", "type", "time_ms"])

        for i, record in enumerate(records):
            dish_id = record["dish_id"]
            npy_path = PROJECT_ROOT / record["rgbd_path"]
            
            try:
                start_time = time.time()
                
                # 1. Load artifact
                rgbd = np.load(npy_path) # (4, 224, 224)
                # Channel 0-2: RGB (normalized), Channel 3: Depth (meters)
                rgb = (np.transpose(rgbd[:3], (1, 2, 0)) * 255).astype(np.uint8)
                depth = rgbd[3]

                # 2. Segment (on the fly since we didn't save masks)
                # Volume estimation REQUIRES a mask
                masks = segmenter.segment(rgb)
                if not masks:
                    logger.warning(f"[{i+1}/{len(records)}] {dish_id}: No segments found")
                    writer.writerow([dish_id, 0.0, 0.0, 0.0, "none", 0.0])
                    continue
                
                # Use the largest mask for volume estimation (assuming single dish focal point)
                main_mask = masks[0]["segmentation"]

                # 3. Volume estimation
                pc = estimator.project_to_pc(depth, main_mask)
                # Convert Z to height above tabletop (default 0.35m)
                pc_h = estimator.get_food_heights(pc)
                
                vol_m3, area_m2, vtype = estimator.estimate_volume(pc_h)
                
                # Convert to cm3 (1 m3 = 1,000,000 cm3) & cm2 (1 m2 = 10,000 cm2)
                vol_cm3 = vol_m3 * 1_000_000
                area_cm2 = area_m2 * 10_000
                
                elapsed_ms = (time.time() - start_time) * 1000
                stats["total_time"] += elapsed_ms
                stats["success"] += 1
                
                writer.writerow([
                    dish_id,
                    round(vol_cm3, 2),
                    round(area_cm2, 2),
                    1.0, # Confidence placeholder
                    vtype,
                    round(elapsed_ms, 1)
                ])

                if (i + 1) % 10 == 0 or (i + 1) == len(records):
                    logger.info(f"[{i+1}/{len(records)}] Processed {dish_id}: {vol_cm3:.2f} cm3 ({vtype})")

            except Exception as e:
                logger.error(f"[{i+1}/{len(records)}] Failed {dish_id}: {e}")
                stats["failed"] += 1

    # Cleanup segmenter (VRAM)
    segmenter.unload()

    logger.info("=" * 60)
    logger.info(f"Volume Feature Generation Complete")
    logger.info(f"  Success: {stats['success']}")
    logger.info(f"  Failed:  {stats['failed']}")
    if stats["success"] > 0:
        avg_time = stats["total_time"] / stats["success"]
        logger.info(f"  Avg Time: {avg_time:.1f} ms/image")
    logger.info(f"  Output:  {out_csv_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
