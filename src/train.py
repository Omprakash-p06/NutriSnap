"""Main training script for NutriSnap Nutrition Regressor.

Executes a 5-fold cross-validation training loop using the baseline configuration.
"""
import argparse
import os
import sys
from pathlib import Path

import torch
import yaml
from torch.utils.data import DataLoader

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.dataset import NutriSnapDataset, collate_fn
from nutrisnap.models.nutrition_regressor import get_model
from nutrisnap.training.trainer import NutritionTrainer
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Train NutriSnap Nutrition Regressor")
    parser.add_argument("--config", default="configs/experiment/baseline.yaml", help="Path to config")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of samples for testing")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs")
    args = parser.parse_args()

    cfg = load_config(args.config)
    exp_cfg = cfg["experiment"]
    
    # Override epochs if provided
    if args.epochs:
        exp_cfg["epochs"] = args.epochs
    
    # Load model config separately
    model_cfg = load_config(PROJECT_ROOT / exp_cfg["model_config"])
    
    # Setup output directory
    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / exp_cfg["name"]
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting experiment: {exp_cfg['name']}")
    logger.info(f"Targeting {exp_cfg['folds']} folds")

    for fold in range(exp_cfg["folds"]):
        logger.info(f"--- FOLD {fold} ---")
        
        # 1. Initialize Dataset & Dataloaders
        # Split files: train_fold_0.txt, val_fold_0.txt
        train_split = Path(exp_cfg["split_dir"]) / f"train_fold_{fold}.txt"
        val_split = Path(exp_cfg["split_dir"]) / f"val_fold_{fold}.txt"
        
        if not train_split.exists():
            logger.error(f"Split file not found: {train_split}")
            continue

        train_ds = NutriSnapDataset(
            rgbd_dir=PROJECT_ROOT / exp_cfg["rgbd_dir"],
            split_file=PROJECT_ROOT / train_split,
            metadata_csv=PROJECT_ROOT / exp_cfg["metadata_csv"],
            volume_features_csv=PROJECT_ROOT / exp_cfg["volume_features_csv"]
        )
        
        val_ds = NutriSnapDataset(
            rgbd_dir=PROJECT_ROOT / exp_cfg["rgbd_dir"],
            split_file=PROJECT_ROOT / val_split,
            metadata_csv=PROJECT_ROOT / exp_cfg["metadata_csv"],
            volume_features_csv=PROJECT_ROOT / exp_cfg["volume_features_csv"]
        )

        if args.limit:
            train_ds.dish_ids = train_ds.dish_ids[:args.limit]
            val_ds.dish_ids = val_ds.dish_ids[:args.limit]

        train_loader = DataLoader(
            train_ds, 
            batch_size=exp_cfg["batch_size"], 
            shuffle=True, 
            num_workers=4,
            collate_fn=collate_fn
        )
        val_loader = DataLoader(
            val_ds, 
            batch_size=exp_cfg["batch_size"], 
            shuffle=False, 
            num_workers=2,
            collate_fn=collate_fn
        )

        # 2. Initialize Model, Optimizer, Trainer
        model = get_model(model_cfg)
        optimizer = torch.optim.AdamW(
            model.parameters(), 
            lr=float(exp_cfg["learning_rate"]),
            weight_decay=float(exp_cfg["weight_decay"])
        )
        
        trainer = NutritionTrainer(
            model=model,
            optimizer=optimizer,
            use_amp=exp_cfg["use_amp"],
            grad_accum_steps=exp_cfg["grad_accum_steps"]
        )

        # 3. Training Loop
        best_val_loss = float("inf")
        for epoch in range(exp_cfg["epochs"]):
            train_metrics = trainer.train_epoch(train_loader, epoch)
            val_metrics = trainer.validate(val_loader)
            
            logger.info(
                f"Fold {fold} Epoch {epoch}: "
                f"Train Loss: {train_metrics['loss']:.4f} | "
                f"Val Loss: {val_metrics['loss']:.4f} | "
                f"Val MAE (Cal): {val_metrics['mae'][0]:.1f}"
            )
            
            # Save best checkpoint
            if val_metrics["loss"] < best_val_loss:
                best_val_loss = val_metrics["loss"]
                checkpoint_path = checkpoint_dir / f"best_fold_{fold}.pth"
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": best_val_loss,
                    "val_metrics": val_metrics
                }, checkpoint_path)
                logger.info(f"New best model saved for fold {fold}")

    logger.info("Training complete.")


if __name__ == "__main__":
    main()
