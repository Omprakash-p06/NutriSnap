import sys
import pandas as pd
from pathlib import Path
import torch
import numpy as np
from tqdm import tqdm
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.pipeline.volume import VolumeEstimator
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

def generate_volume_features(features_dir, output_csv, config_path):
    features_dir = Path(features_dir)
    output_csv = Path(output_csv)
    
    if not features_dir.exists():
        logger.error(f"Features directory not found: {features_dir}")
        return

    estimator = VolumeEstimator(config_path=config_path)
    
    # We only compute volume for overhead views as they have reliable depth
    depth_files = list(features_dir.glob("*_overhead_depth.pt"))
    if not depth_files:
        # Try any depth file if no overhead found (e.g. for small subsets)
        depth_files = list(features_dir.glob("*_depth.pt"))
        
    logger.info(f"Found {len(depth_files)} depth files.")
    
    results = []
    for depth_path in tqdm(depth_files, desc="Estimating Volume"):
        stem = depth_path.stem.replace("_depth", "")
        # Extract dish_id (e.g. dish_1550704750)
        dish_id = "_".join(stem.split("_")[:2])
        
        try:
            depth_tensor = torch.load(depth_path)
            depth_np = depth_tensor.squeeze().numpy()
            
            # Use depth > 0 as the mask since it's already masked by SAM in preprocess_full.py
            mask = (depth_np > 0).astype(np.uint8)
            
            if mask.sum() < 100:
                # logger.debug(f"Skipping {stem}: too few masked points")
                continue
                
            pc = estimator.project_to_pc(depth_np, mask)
            if pc.size > 0:
                pc_h = estimator.get_food_heights(pc)
                vol_m3, area_m2, _ = estimator.estimate_volume(pc_h)
                
                # Convert to cm3 and cm2
                vol_cm3 = vol_m3 * 1_000_000
                area_cm2 = area_m2 * 10_000
                
                results.append({
                    "dish_id": dish_id,
                    "volume_cm3": vol_cm3,
                    "area_cm2": area_cm2,
                    "confidence": 1.0 # Placeholder
                })
        except Exception as e:
            logger.debug(f"Failed to process {stem}: {e}")

    if not results:
        logger.warning("No volume features generated.")
        return

    df = pd.DataFrame(results)
    # Average across multiple views of the same dish if they exist
    df = df.groupby("dish_id").mean().reset_index()
    
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info(f"Saved volume features for {len(df)} dishes to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate volume features CSV from preprocessed depth tensors")
    parser.add_argument("--features-dir", default="data/processed/features")
    parser.add_argument("--output-csv", default="data/processed/features/volume_features.csv")
    parser.add_argument("--config", default="configs/pipeline/volume.yaml")
    args = parser.parse_args()
    
    generate_volume_features(args.features_dir, args.output_csv, args.config)
