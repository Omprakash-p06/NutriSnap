"""Main training script for NutriSnap Nutrition Regressor v2.

Runs N-fold cross-validation using the ensemble_5fold config.
Supports 3-phase transfer learning and early stopping.

Usage:
    .venv\\Scripts\\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml
    .venv\\Scripts\\python.exe src/train.py --config configs/experiment/ensemble_5fold.yaml --limit 20 --epochs 1
"""
import argparse
import json
import sys
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn
import yaml
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.augmentation import get_train_augmentation, get_val_augmentation
from nutrisnap.data.dataset import NutriSnapDataset, collate_fn
from nutrisnap.models.loss import UncertaintyWeightedLoss
from nutrisnap.models.nutrition_regressor import get_model
from nutrisnap.training.trainer import NutritionTrainer
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_fold_split_files(exp_cfg: dict, fold: int) -> tuple[Path, Path]:
    """Resolve train/val split files for a given fold.

    Tries cv_folds.json first (full dataset), then falls back to
    train_fold_N.txt / val_fold_N.txt files.
    """
    split_dir = Path(exp_cfg["split_dir"])

    # Prefer cv_folds.json for full dataset training
    cv_folds_path = split_dir / "cv_folds.json"
    if cv_folds_path.exists():
        with open(cv_folds_path) as f:
            cv_folds = json.load(f)
        # Write temporary split files for this fold
        fold_data = (
            cv_folds[fold]
            if isinstance(cv_folds, list)
            else cv_folds.get(str(fold), {})
        )
        train_ids = fold_data.get("train", [])
        val_ids = fold_data.get("val", [])

        train_tmp = split_dir / f"_tmp_train_fold_{fold}.txt"
        val_tmp = split_dir / f"_tmp_val_fold_{fold}.txt"
        train_tmp.write_text("\n".join(train_ids) + "\n")
        val_tmp.write_text("\n".join(val_ids) + "\n")
        return train_tmp, val_tmp

    # Fallback: static per-fold files
    return (
        split_dir / f"train_fold_{fold}.txt",
        split_dir / f"val_fold_{fold}.txt",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Train NutriSnap dual-branch regressor"
    )
    parser.add_argument("--config", default="configs/experiment/ensemble_5fold.yaml")
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit samples per fold (for dry run)"
    )
    parser.add_argument("--epochs", type=int, default=None, help="Override epoch count")
    args = parser.parse_args()

    cfg = load_config(args.config)
    exp_cfg = cfg["experiment"]
    if args.epochs:
        exp_cfg["epochs"] = args.epochs

    model_cfg = load_config(PROJECT_ROOT / exp_cfg["model_config"])

    checkpoint_dir = PROJECT_ROOT / "models" / "checkpoints" / exp_cfg["name"]
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting experiment: {exp_cfg['name']}")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if torch.cuda.is_available():
        cudnn.benchmark = True
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDNN Benchmark: Enabled")

    logger.info(
        f"Folds: {exp_cfg['folds']} | Epochs: {exp_cfg['epochs']} | Device: {device}"
    )

    for fold in range(exp_cfg["folds"]):
        logger.info(f"\n{'='*60}")
        logger.info(f"FOLD {fold + 1}/{exp_cfg['folds']}")
        logger.info(f"{'='*60}")

        train_split, val_split = get_fold_split_files(exp_cfg, fold)

        if not train_split.exists():
            logger.error(
                f"Train split not found: {train_split}. Run scripts/generate_splits.py first."
            )
            continue
        if not val_split.exists():
            logger.error(f"Val split not found: {val_split}")
            continue

        features_dir = PROJECT_ROOT / exp_cfg["features_dir"]
        metadata_csv = PROJECT_ROOT / exp_cfg["metadata_csv"]
        volume_csv = PROJECT_ROOT / exp_cfg.get(
            "volume_features_csv", "data/processed/features/volume_features.csv"
        )

        train_ds = NutriSnapDataset(
            features_dir=features_dir,
            split_file=train_split,
            metadata_csv=metadata_csv,
            volume_features_csv=volume_csv,
            transform=get_train_augmentation(),
        )
        val_ds = NutriSnapDataset(
            features_dir=features_dir,
            split_file=val_split,
            metadata_csv=metadata_csv,
            volume_features_csv=volume_csv,
            transform=get_val_augmentation(),
        )

        if args.limit:
            train_ds.sample_stems = train_ds.sample_stems[: args.limit]
            val_ds.sample_stems = val_ds.sample_stems[
                : min(args.limit // 4, len(val_ds.sample_stems))
            ]

        if len(train_ds) == 0:
            logger.error(f"No training samples for fold {fold}. Skipping.")
            continue

        train_loader = DataLoader(
            train_ds,
            batch_size=exp_cfg["batch_size"],
            shuffle=True,
            num_workers=exp_cfg.get("num_workers", 0),  # Default to 0 on Windows
            pin_memory=True,
            collate_fn=collate_fn,
        )

        val_loader = None
        if len(val_ds) > 0:
            val_loader = DataLoader(
                val_ds,
                batch_size=exp_cfg["batch_size"],
                shuffle=False,
                num_workers=exp_cfg.get("num_workers", 0),  # Default to 0 on Windows
                pin_memory=True,
                collate_fn=collate_fn,
            )
        else:
            logger.warning(
                f"Fold {fold} has no validation samples. Skipping validation for this fold."
            )

        # Model + Loss
        model = get_model(model_cfg)
        criterion = UncertaintyWeightedLoss(n_tasks=4)

        trainer = NutritionTrainer(
            model=model,
            criterion=criterion,
            use_amp=exp_cfg.get("use_amp", True),
            grad_accum_steps=exp_cfg.get("grad_accum_steps", 4),
            lr_heads=float(exp_cfg.get("lr_heads", 1e-4)),
            lr_backbone_partial=float(exp_cfg.get("lr_backbone_partial", 1e-5)),
            lr_backbone_full=float(exp_cfg.get("lr_backbone_full", 1e-6)),
            weight_decay=float(exp_cfg.get("weight_decay", 1e-5)),
            phase1_epochs=exp_cfg.get("phase1_epochs", 10),
            phase2_epochs=exp_cfg.get("phase2_epochs", 20),
            max_epochs=exp_cfg["epochs"],
            early_stopping_patience=exp_cfg.get("early_stopping_patience", 10),
        )
        trainer.setup_fold()

        for epoch in range(exp_cfg["epochs"]):
            train_metrics = trainer.train_epoch(train_loader, epoch)

            if val_loader is not None:
                val_metrics = trainer.validate(val_loader)
                improved = trainer.is_improved(val_metrics["loss"])
                logger.info(
                    f"Fold {fold} | Epoch {epoch:3d} | "
                    f"Train Loss: {train_metrics['loss']:.4f} | "
                    f"Val Loss: {val_metrics['loss']:.4f} | "
                    f"MAE Cal: {val_metrics['mae'][0]:.1f} kcal | "
                    f"MAPE Cal: {val_metrics['mape'][0]:.1f}% | "
                    f"{'[BEST]' if improved else ''}"
                )

                if improved:
                    torch.save(
                        {
                            "epoch": epoch,
                            "fold": fold,
                            "model_state_dict": model.state_dict(),
                            "val_loss": trainer.best_val_loss,
                            "val_metrics": val_metrics,
                        },
                        checkpoint_dir / f"best_fold_{fold}.pth",
                    )

                if trainer.should_stop_early:
                    logger.info(
                        f"Early stopping at epoch {epoch} (patience={trainer.early_stopping_patience})"
                    )
                    break
            else:
                # No validation data — log train-only and save checkpoint every epoch
                logger.info(
                    f"Fold {fold} | Epoch {epoch:3d} | "
                    f"Train Loss: {train_metrics['loss']:.4f} | "
                    f"(no validation data)"
                )
                torch.save(
                    {
                        "epoch": epoch,
                        "fold": fold,
                        "model_state_dict": model.state_dict(),
                        "val_loss": float("inf"),
                        "val_metrics": {},
                    },
                    checkpoint_dir / f"best_fold_{fold}.pth",
                )

    logger.info("\nTraining complete. Checkpoints saved to:")
    logger.info(f"  {checkpoint_dir}")


if __name__ == "__main__":
    main()
