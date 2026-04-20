import argparse
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torchvision.transforms as T
from sklearn.isotonic import IsotonicRegression
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import get_linear_schedule_with_warmup

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nutrisnap.models.efficientnet_regressor import EfficientNetRegressor
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


class CompositeDataset(Dataset):
    def __init__(self, ids, features_dir, dishes_df, is_train=False):
        self.ids = ids
        self.features_dir = Path(features_dir)
        # Ensure dish_id is string for matching
        dishes_df["dish_id"] = dishes_df["dish_id"].astype(str)
        self.labels = dishes_df.set_index("dish_id")["total_mass"].to_dict()

        # Load volumes
        volumes_df = pd.read_csv("data/processed/volumes.csv")
        self.volumes = volumes_df.set_index("filename")["volume"].to_dict()

        # Find all available composite files for these IDs
        self.samples = []
        for did in ids:
            # We look for all files matching {did}_*_composite.pt
            files = list(self.features_dir.glob(f"{did}_*_composite.pt"))
            for f in files:
                if did in self.labels and f.name in self.volumes:
                    self.samples.append((f, self.labels[did], self.volumes[f.name]))
                else:
                    logger.warning(f"Missing label or volume for dish {did} / {f.name}")

        self.is_train = is_train

        # Aggressive spatial augmentations for small dataset
        self.spatial_aug = T.Compose(
            [
                T.RandomHorizontalFlip(p=0.5),
                T.RandomVerticalFlip(p=0.5),
                T.RandomRotation(degrees=30),
                T.RandomAffine(degrees=0, shear=15),
                T.RandomResizedCrop(size=(224, 224), scale=(0.6, 1.0), antialias=True),
            ]
        )

        # Aggressive color augmentations
        self.color_aug = T.Compose(
            [
                T.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.15),
                T.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 2.0)),
            ]
        )

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        feat_path, label, vol = self.samples[idx]
        pixel_values = torch.load(feat_path, weights_only=True)

        if self.is_train:
            # 1. Apply spatial transforms to all 5 channels
            pixel_values = self.spatial_aug(pixel_values)

            # 2. Apply color transforms only to the RGB channels (indices 0, 1, 2)
            rgb = pixel_values[:3, :, :]
            mask_depth = pixel_values[3:, :, :]
            rgb = self.color_aug(rgb)

            # Recombine
            pixel_values = torch.cat([rgb, mask_depth], dim=0)

            # 3. Aggressive Gaussian Noise (Strategy: Noise Invariant Training)
            if torch.rand(1) < 0.3:
                noise = torch.randn_like(pixel_values) * 0.05
                pixel_values = pixel_values + noise

        # Apply log1p transformation to handle skewed mass distributions
        label_tensor = torch.tensor([label], dtype=torch.float32)
        log_label = torch.log1p(label_tensor)
        volume_tensor = torch.tensor([vol], dtype=torch.float32)

        return pixel_values, volume_tensor, log_label


def pearson_correlation_loss(x, y):
    """Computes (1 - Pearson Correlation) as a loss."""
    x_mean = torch.mean(x)
    y_mean = torch.mean(y)
    x_centered = x - x_mean
    y_centered = y - y_mean

    # Covariance
    numerator = torch.sum(x_centered * y_centered)

    # Variance
    denominator = torch.sqrt(torch.sum(x_centered**2)) * torch.sqrt(
        torch.sum(y_centered**2)
    )

    # Pearson Correlation Coefficient (r)
    if denominator < 1e-8:
        return torch.tensor(0.0, device=x.device, requires_grad=True)

    r = numerator / denominator
    return 1 - r


def train_one_epoch(
    model, loader, optimizer, scheduler, device, epoch, limit_batches=None
):
    model.train()
    total_loss = 0
    pbar = tqdm(loader, desc=f"Epoch {epoch}")
    for i, (x, v, y) in enumerate(pbar):
        if limit_batches and i >= limit_batches:
            break
        x, v, y = x.to(device), v.to(device), y.to(device)
        optimizer.zero_grad()
        pred = model(x, v)

        # Combined Loss: MSE + Pearson Correlation Loss
        mse_loss = nn.MSELoss()(pred, y)

        # Only compute correlation loss if batch size > 1
        if x.size(0) > 1:
            corr_loss = pearson_correlation_loss(pred, y)
            # Increased weight of correlation loss to 5.0 (from 2.0) to aggressively prioritize ranking
            loss = mse_loss + 5.0 * corr_loss
        else:
            loss = mse_loss

        loss.backward()
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        pbar.set_postfix(loss=loss.item())

    return total_loss / (limit_batches if limit_batches else len(loader))


def validate(model, loader, device, limit_batches=None):
    model.eval()
    total_mae = 0
    count = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for i, (x, v, y) in enumerate(loader):
            if limit_batches and i >= limit_batches:
                break
            x, v, y = x.to(device), v.to(device), y.to(device)
            pred = model(x, v)

            # Convert back from log scale to calculate actual MAE in grams
            pred_grams = torch.expm1(pred)
            y_grams = torch.expm1(y)

            total_mae += torch.abs(pred_grams - y_grams).sum().item()
            count += x.size(0)

            all_preds.extend(pred_grams.cpu().numpy().flatten())
            all_targets.extend(y_grams.cpu().numpy().flatten())

    mae = total_mae / count if count > 0 else 0

    # Calculate Spearman Correlation and R2
    spearman_corr = 0
    r2 = 0
    if len(all_preds) > 1:
        from scipy.stats import spearmanr

        spearman_corr = spearmanr(all_preds, all_targets).correlation

        import numpy as np
        from sklearn.metrics import r2_score

        r2 = r2_score(all_targets, all_preds)

    return mae, spearman_corr, r2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mvp-ids", default="data/splits/mvp_subset_ids.txt")
    parser.add_argument("--features-dir", default="data/processed/features")
    parser.add_argument("--dishes-csv", default="data/interim/dishes.csv")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument(
        "--output", default="models/checkpoints/efficientnet_mass_regressor.pth"
    )
    parser.add_argument("--limit-batches", type=int, default=None)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load IDs
    ids_path = Path(args.mvp_ids)
    if not ids_path.exists():
        logger.error(f"IDs file not found: {args.mvp_ids}")
        return

    ids = [l.strip() for l in ids_path.read_text().splitlines() if l.strip()]
    dishes_df = pd.read_csv(args.dishes_csv)

    # Split MVP into train/val (simple split for MVP)
    n_train = int(len(ids) * 0.8)
    train_ids = ids[:n_train]
    val_ids = ids[n_train:]

    train_ds = CompositeDataset(train_ids, args.features_dir, dishes_df, is_train=True)
    val_ds = CompositeDataset(val_ids, args.features_dir, dishes_df, is_train=False)

    if len(train_ds) == 0:
        logger.error("No training samples found. Check features-dir and mvp-ids.")
        return

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    logger.info(f"Train samples: {len(train_ds)}, Val samples: {len(val_ds)}")

    model = EfficientNetRegressor().to(device)

    # ---------------------------------------------------------
    # TRANSFER LEARNING: FREEZE BACKBONE
    # ---------------------------------------------------------
    logger.info("Freezing EfficientNet backbone...")
    for param in model.backbone.parameters():
        param.requires_grad = False

    # Ensure the 5->3 channel projection is TRAINABLE
    for param in model.channel_proj.parameters():
        param.requires_grad = True

    # Verify frozen parameters
    trainable_params = filter(lambda p: p.requires_grad, model.parameters())
    num_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    num_total = sum(p.numel() for p in model.parameters())
    logger.info(
        f"Trainable parameters: {num_trainable:,} / {num_total:,} ({num_trainable/num_total:.2%})"
    )

    optimizer = AdamW(trainable_params, lr=args.lr)

    num_training_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
    )

    best_mae = float("inf")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(
            model, train_loader, optimizer, scheduler, device, epoch, args.limit_batches
        )
        mae, spearman, r2 = validate(model, val_loader, device, args.limit_batches)

        logger.info(
            f"Epoch {epoch}: Loss={loss:.4f}, Val MAE={mae:.2f}g, Spearman={spearman:.4f}, R2={r2:.4f}"
        )

        if mae < best_mae and mae > 0:
            best_mae = mae
            torch.save(model.state_dict(), args.output)
            logger.info(f"Saved best model with MAE={best_mae:.2f}g")

    # ---------------------------------------------------------
    # POST-TRAINING CALIBRATION (Strategy: Variance/Bias correction)
    # ---------------------------------------------------------
    logger.info("Performing post-training calibration...")
    try:
        model.load_state_dict(torch.load(args.output, weights_only=True))
        model.eval()

        all_val_preds = []
        all_val_targets = []
        with torch.no_grad():
            for x, v, y in val_loader:
                x, v, y = x.to(device), v.to(device), y.to(device)
                pred = model(x, v)
                all_val_preds.extend(torch.expm1(pred).cpu().numpy().flatten())
                all_val_targets.extend(torch.expm1(y).cpu().numpy().flatten())

        all_val_preds = np.array(all_val_preds)
        all_val_targets = np.array(all_val_targets)

        # Fit Isotonic Regression to calibrate predictions
        calibrator = IsotonicRegression(out_of_bounds="clip")
        calibrator.fit(all_val_preds, all_val_targets)

        cal_path = args.output.replace(".pth", "_calibrator.joblib")
        joblib.dump(calibrator, cal_path)
        logger.info(f"Saved calibrator to {cal_path}")

        # Evaluate calibrated
        cal_preds = calibrator.transform(all_val_preds)
        from scipy.stats import spearmanr
        from sklearn.metrics import mean_absolute_error, r2_score

        cal_mae = mean_absolute_error(all_val_targets, cal_preds)
        cal_spearman = spearmanr(all_val_targets, cal_preds).correlation
        cal_r2 = r2_score(all_val_targets, cal_preds)

        logger.info(
            f"Calibrated Val Metrics: MAE={cal_mae:.2f}g, Spearman={cal_spearman:.4f}, R2={cal_r2:.4f}"
        )
    except Exception as e:
        logger.warning(f"Calibration failed: {e}")


if __name__ == "__main__":
    main()
