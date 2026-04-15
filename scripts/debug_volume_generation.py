"""Debug script to verify volume generation logic with a Mock Segmenter.

Allows testing the volume feature pipeline without waiting for 2.4GB SAM weights.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.pipeline.volume import VolumeEstimator
from nutrisnap.utils.config_loader import load_data_config
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

class MockSegmenter:
    """Returns a full-image mask for testing."""
    def segment(self, image):
        H, W = image.shape[:2]
        # Create a circle mask in the center
        mask = np.zeros((H, W), dtype=np.uint8)
        center = (H // 2, W // 2)
        radius = min(H, W) // 3
        y, x = np.ogrid[:H, :W]
        dist_from_center = np.sqrt((x - center[1])**2 + (y - center[0])**2)
        mask[dist_from_center <= radius] = 255
        return [{"segmentation": mask}]
    
    def unload(self):
        pass

def main():
    parser = argparse.ArgumentParser(description="Debug volume features")
    parser.add_argument("--config", default="configs/data/data_config.yaml")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    data_cfg = load_data_config(args.config)
    processed_dir = Path(data_cfg.processed_dir)
    rgbd_dir = processed_dir / "rgbd"
    manifest_path = rgbd_dir / "manifest.csv"

    if not manifest_path.exists():
        logger.error("Manifest not found")
        return

    segmenter = MockSegmenter()
    estimator = VolumeEstimator()

    with open(manifest_path, "r") as f:
        reader = csv.DictReader(f)
        records = list(reader)[:args.limit]

    logger.info(f"DEBUG: Generating features with MockSegmenter for {len(records)} artifacts...")

    for i, record in enumerate(records):
        dish_id = record["dish_id"]
        npy_path = PROJECT_ROOT / record["rgbd_path"]
        
        rgbd = np.load(npy_path)
        depth = rgbd[3]
        rgb = (np.transpose(rgbd[:3], (1, 2, 0)) * 255).astype(np.uint8)

        masks = segmenter.segment(rgb)
        main_mask = masks[0]["segmentation"]

        pc = estimator.project_to_pc(depth, main_mask)
        pc_h = estimator.get_food_heights(pc)
        vol_m3, area_m2, vtype = estimator.estimate_volume(pc_h)
        
        vol_cm3 = vol_m3 * 1_000_000
        logger.info(f"  {dish_id}: {vol_cm3:.2f} cm3 ({vtype})")

    logger.info("DEBUG: Volume generation logic verified.")

if __name__ == "__main__":
    main()
