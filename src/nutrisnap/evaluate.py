import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nutrisnap.models.vit_regressor import ViTRegressor
from nutrisnap.training.train_vit import CompositeDataset
from nutrisnap.utils.logger import get_logger
from nutrisnap.utils.metrics import (
    calorie_mae,
    calorie_mape,
    r2_score,
    spearman_correlation,
)

logger = get_logger(__name__)


def evaluate(model, loader, device):
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for x, v, y in tqdm(loader, desc="Evaluating"):
            x, v, y = x.to(device), v.to(device), y.to(device)
            pred = model(x, v)

            # Inverse log1p transform to return to gram scale
            pred_grams = torch.expm1(pred)
            y_grams = torch.expm1(y)

            all_preds.extend(pred_grams.cpu().numpy().flatten())
            all_targets.extend(y_grams.cpu().numpy().flatten())

    return all_targets, all_preds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mvp-ids", default="datasets/splits/mvp_subset_ids.txt")
    parser.add_argument("--features-dir", default="datasets/processed/features")
    parser.add_argument("--dishes-csv", default="datasets/interim/dishes.csv")
    parser.add_argument("--checkpoint", default="checkpoints/vit_mass_regressor.pth")
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load IDs
    ids_path = Path(args.mvp_ids)
    ids = [l.strip() for l in ids_path.read_text().splitlines() if l.strip()]
    dishes_df = pd.read_csv(args.dishes_csv)

    # Use the exact same validation split logic as training
    n_train = int(len(ids) * 0.8)
    val_ids = ids[n_train:]

    val_ds = CompositeDataset(val_ids, args.features_dir, dishes_df, is_train=False)
    if len(val_ds) == 0:
        logger.error("No validation samples found!")
        return

    val_loader = DataLoader(val_ds, batch_size=args.batch_size)
    logger.info(f"Loaded {len(val_ds)} validation samples.")

    # Load Model
    model = ViTRegressor().to(device)
    if not os.path.exists(args.checkpoint):
        logger.error(f"Checkpoint not found: {args.checkpoint}")
        return

    model.load_state_dict(
        torch.load(args.checkpoint, map_location=device, weights_only=True)
    )
    logger.info("Loaded ViT Regressor weights successfully.")

    # Evaluate
    y_true, y_pred = evaluate(model, val_loader, device)

    # Calculate Metrics
    # (Note: These are MASS metrics in grams, not calories. Since calorie mapping is linear via densities, the correlation metrics remain identical)
    mae = calorie_mae(y_true, y_pred)
    mape = calorie_mape(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    spearman = spearman_correlation(y_true, y_pred)

    print("-" * 50)
    print("EVALUATION RESULTS (MASS / GRAMS)")
    print("-" * 50)
    print(f"MAE:       {mae:.2f} g")
    print(f"MAPE:      {mape:.2f} %")
    print(f"R2 Score:  {r2:.4f}")
    print(f"Spearman:  {spearman:.4f}")
    print("-" * 50)


if __name__ == "__main__":
    main()
