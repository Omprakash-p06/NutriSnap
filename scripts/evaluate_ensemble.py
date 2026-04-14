"""Evaluate the Nutrition Ensemble on the test set.

Usage:
    python scripts/evaluate_ensemble.py --checkpoint-dir models/checkpoints/baseline_v1
"""
import argparse
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.dataset import NutriSnapDataset, collate_fn
from nutrisnap.pipeline.inference import NutritionPredictor
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Nutrition Ensemble")
    parser.add_argument("--checkpoint-dir", required=True, help="Directory containing fold checkpoints")
    parser.add_argument("--model-config", default="configs/models/nutrition_v1.yaml")
    parser.add_argument("--experiment-config", default="configs/experiment/baseline.yaml")
    args = parser.parse_args()

    # 1. Setup Predictor
    predictor = NutritionPredictor(
        checkpoint_dir=PROJECT_ROOT / args.checkpoint_dir,
        model_config_path=PROJECT_ROOT / args.model_config
    )

    # 2. Setup Test Dataset
    with open(PROJECT_ROOT / args.experiment_config) as f:
        import yaml
        exp_cfg = yaml.safe_load(f)["experiment"]

    test_split = Path(exp_cfg["split_dir"]) / "test_ids.txt"
    test_ds = NutriSnapDataset(
        rgbd_dir=PROJECT_ROOT / exp_cfg["rgbd_dir"],
        split_file=PROJECT_ROOT / test_split,
        metadata_csv=PROJECT_ROOT / exp_cfg["metadata_csv"],
        volume_features_csv=PROJECT_ROOT / exp_cfg["volume_features_csv"]
    )
    
    test_loader = DataLoader(
        test_ds, 
        batch_size=1, 
        shuffle=False, 
        num_workers=2,
        collate_fn=collate_fn
    )

    logger.info(f"Evaluating ensemble on {len(test_ds)} test samples...")

    all_preds = []
    all_targets = []

    for batch in tqdm(test_loader, desc="Testing"):
        rgbd = batch["rgbd"]
        scalars = batch["scalar_features"]
        targets = batch["targets"]
        
        # Predict
        res = predictor.predict(rgbd, scalars)
        preds = torch.tensor([[res["calories"], res["fat"], res["carbs"], res["protein"]]])
        
        all_preds.append(preds)
        all_targets.append(targets)

    if not all_preds:
        logger.error("No test samples were processed.")
        return

    all_preds = torch.cat(all_preds)
    all_targets = torch.cat(all_targets)

    # Calculate metrics
    mae = torch.mean(torch.abs(all_preds - all_targets), dim=0)
    mape = torch.mean(torch.abs((all_preds - all_targets) / (all_targets + 1e-6)), dim=0) * 100

    print("\n" + "="*40)
    print("ENSEMBLE TEST RESULTS")
    print("="*40)
    macros = ["Calories", "Fat", "Carbs", "Protein"]
    for i, macro in enumerate(macros):
        print(f"{macro:10}: MAE={mae[i]:.2f}, MAPE={mape[i]:.2f}%")
    print("="*40)


if __name__ == "__main__":
    main()
