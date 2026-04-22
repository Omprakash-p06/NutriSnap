#!/usr/bin/env python3
"""NutriSnap Post-Training Verification — evaluate + smoke check in one run.

Replaces the separate evaluate_ensemble.py + smoke_check_pipeline.py scripts.

Runs two stages after training:
  Stage 1 – Evaluate:    ensemble MAE, MAPE, R², RMSE, Bias, Spearman, std dev
  Stage 2 – Smoke Check: single image end-to-end pipeline verification

Usage:
    .venv\\Scripts\\python.exe scripts/verify_results.py
    .venv\\Scripts\\python.exe scripts/verify_results.py --stage eval    # eval only
    .venv\\Scripts\\python.exe scripts/verify_results.py --stage smoke   # smoke only
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Ensemble Evaluation
# ──────────────────────────────────────────────────────────────────────────────


def stage_evaluate(config: dict) -> dict:
    """Load all fold checkpoints, run inference on test set, report metrics."""
    logger.info("=" * 60)
    logger.info("STAGE 1 — ENSEMBLE EVALUATION")
    logger.info("=" * 60)

    from nutrisnap.data.augmentation import get_val_augmentation
    from nutrisnap.data.dataset import NutriSnapDataset, collate_fn
    from nutrisnap.models.nutrition_regressor import get_model

    exp_cfg = config.get("experiment", config)  # handle both wrapping styles
    features_dir = Path(exp_cfg["features_dir"])
    splits_dir = Path(exp_cfg["split_dir"])
    metadata_csv = Path(exp_cfg["metadata_csv"])
    volume_csv = exp_cfg.get("volume_features_csv")
    checkpoint_dir = Path("checkpoints") / exp_cfg["name"]
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"  Device: {device}")

    test_split = splits_dir / "test_ids.txt"
    if not test_split.exists():
        logger.error(f"Test split not found: {test_split}. Run prepare_data.py first.")
        return {}

    test_ds = NutriSnapDataset(
        features_dir=features_dir,
        split_file=test_split,
        metadata_csv=metadata_csv,
        volume_features_csv=volume_csv,
        transform=get_val_augmentation(),
    )

    if len(test_ds) == 0:
        logger.error("No test samples found. Run preprocess_full.py first.")
        return {}

    from torch.utils.data import DataLoader

    loader = DataLoader(
        test_ds, batch_size=8, shuffle=False, collate_fn=collate_fn, num_workers=2
    )

    model_cfg_path = Path(
        exp_cfg.get("model_config", "configs/models/efficientnet_v2_b0.yaml")
    )
    with open(model_cfg_path) as f:
        model_cfg = yaml.safe_load(f)

    # Collect predictions from all fold checkpoints
    all_preds: list[torch.Tensor] = []
    fold_weights: list[float] = []
    checkpoints = sorted(checkpoint_dir.glob("best_fold_*.pth"))

    if not checkpoints:
        logger.error(f"No checkpoints found in {checkpoint_dir}. Run training first.")
        return {}

    logger.info(f"  Found {len(checkpoints)} fold checkpoints")

    for ckpt_path in checkpoints:
        ckpt = torch.load(ckpt_path, map_location=device)
        model = get_model(model_cfg).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        fold_preds = []
        with torch.no_grad():
            for batch in loader:
                rgb = batch["rgb"].to(device)
                depth = batch["depth"].to(device)
                scalars = batch["scalar_features"].to(device)
                preds = model(rgb, depth, scalars)
                fold_preds.append(preds.cpu())

        fold_tensor = torch.cat(fold_preds)  # (N, 4)
        all_preds.append(fold_tensor)
        val_loss = ckpt.get("val_loss", 1.0)
        fold_weights.append(1.0 / max(val_loss, 1e-6))
        logger.info(f"  {ckpt_path.name}: val_loss={val_loss:.4f}")

    # Weighted ensemble
    w = torch.tensor(fold_weights)
    w = w / w.sum()
    ensemble_preds = sum(w[i] * all_preds[i] for i in range(len(all_preds)))

    # Ground truth (already normalized in dataset)
    all_targets = []
    for batch in loader:
        all_targets.append(batch["targets"])
    targets = torch.cat(all_targets)

    # Denormalize both to real units for metrics
    from nutrisnap.data.dataset import TARGET_SCALES

    ensemble_preds = ensemble_preds * TARGET_SCALES
    targets = targets * TARGET_SCALES

    # ── Metrics ──────────────────────────────────────────────────────────────
    NUTRIENTS = ["Calories", "Fat", "Carbs", "Protein"]
    metrics = {}

    for i, name in enumerate(NUTRIENTS):
        p = ensemble_preds[:, i]
        t = targets[:, i]

        mae = torch.mean(torch.abs(p - t)).item()
        mape = torch.mean(torch.abs((p - t) / (t + 1e-6))).item() * 100
        bias = torch.mean(p - t).item()
        rmse = torch.sqrt(torch.mean((p - t) ** 2)).item()
        ss_res = torch.sum((p - t) ** 2).item()
        ss_tot = torch.sum((t - t.mean()) ** 2).item()
        r2 = 1 - ss_res / (ss_tot + 1e-6)

        # Spearman correlation (rank-based)
        p_np = p.numpy()
        t_np = t.numpy()
        p_rank = np.argsort(np.argsort(p_np)).astype(float)
        t_rank = np.argsort(np.argsort(t_np)).astype(float)
        spearman = float(np.corrcoef(p_rank, t_rank)[0, 1])

        std_dev = torch.std(p).item()

        metrics[name] = {
            "MAE": round(mae, 2),
            "MAPE": round(mape, 2),
            "Bias": round(bias, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 4),
            "Spearman": round(spearman, 4),
            "EnsembleStdDev": round(std_dev, 2),
        }

        # Print
        logger.info(f"\n  {name}:")
        logger.info(f"    MAE: {mae:.2f}  MAPE: {mape:.2f}%  Bias: {bias:.2f}")
        logger.info(f"    RMSE: {rmse:.2f}  R²: {r2:.4f}  Spearman: {spearman:.4f}")
        logger.info(f"    Ensemble std dev: {std_dev:.2f}")

    # Calorie-specific targets check
    cal = metrics["Calories"]
    passed = (
        cal["MAE"] <= 40
        and cal["MAPE"] <= 12
        and cal["R2"] >= 0.85
        and cal["Spearman"] >= 0.90
    )
    metrics["_targets_met"] = passed
    logger.info(
        f"\n  Calorie targets (MAE≤40, MAPE≤12%, R²≥0.85, Spearman≥0.90): {'✅ PASSED' if passed else '❌ NOT MET'}"
    )

    # Constant-prediction check
    cal_std = metrics["Calories"]["EnsembleStdDev"]
    if cal_std < 10:
        logger.warning(
            "  ⚠️  Ensemble calorie std dev is very low — possible constant prediction failure mode!"
        )

    # Save report
    report_path = reports_dir / "evaluation_results.json"
    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"\n  Report saved: {report_path}")

    return metrics


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Smoke Check
# ──────────────────────────────────────────────────────────────────────────────


def stage_smoke(config: dict) -> bool:
    """Run a single dish through the full pipeline and confirm it produces valid output."""
    logger.info("=" * 60)
    logger.info("STAGE 2 — END-TO-END SMOKE CHECK")
    logger.info("=" * 60)

    from nutrisnap.data.augmentation import get_val_augmentation
    from nutrisnap.data.dataset import NutriSnapDataset, collate_fn
    from nutrisnap.models.nutrition_regressor import get_model
    from nutrisnap.verification.rule_validator import NutritionValidator

    exp_cfg = config.get("experiment", config)
    features_dir = Path(exp_cfg["features_dir"])
    splits_dir = Path(exp_cfg["split_dir"])
    metadata_csv = Path(exp_cfg["metadata_csv"])
    volume_csv = exp_cfg.get("volume_features_csv")
    checkpoint_dir = Path("checkpoints") / exp_cfg["name"]

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Pick one dish from val set
    val_split = splits_dir / "val_ids.txt"
    if not val_split.exists():
        logger.error("val_ids.txt not found — run prepare_data.py first")
        return False

    val_ds = NutriSnapDataset(
        features_dir=features_dir,
        split_file=val_split,
        metadata_csv=metadata_csv,
        volume_features_csv=volume_csv,
        transform=get_val_augmentation(),
    )

    if len(val_ds) == 0:
        logger.error("No preprocessed val samples — run preprocess_full.py first")
        return False

    batch = collate_fn([val_ds[0]])
    dish_id = batch["dish_ids"][0]
    logger.info(f"  Test dish: {dish_id}")

    # Load first checkpoint
    checkpoints = sorted(checkpoint_dir.glob("best_fold_*.pth"))
    if not checkpoints:
        logger.error("No checkpoints found — run training first")
        return False

    model_cfg_path = Path(
        exp_cfg.get("model_config", "configs/models/efficientnet_v2_b0.yaml")
    )
    with open(model_cfg_path) as f:
        model_cfg = yaml.safe_load(f)

    model = get_model(model_cfg).to(device)
    ckpt = torch.load(str(checkpoints[0]), map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    with torch.no_grad():
        preds = model(
            batch["rgb"].to(device),
            batch["depth"].to(device),
            batch["scalar_features"].to(device),
        )

    # Denormalize predictions to real units
    from nutrisnap.data.dataset import TARGET_SCALES

    preds_real = (preds[0] * TARGET_SCALES.to(device)).tolist()
    cal, fat, carb, prot = preds_real
    prediction = {"calories": cal, "fat": fat, "carbs": carb, "protein": prot}
    targets_real = (batch["targets"][0] * TARGET_SCALES).tolist()

    logger.info(
        f"  Prediction: cal={cal:.1f} fat={fat:.1f} carb={carb:.1f} prot={prot:.1f}"
    )
    logger.info(
        f"  Ground truth: cal={targets_real[0]:.1f} fat={targets_real[1]:.1f} carb={targets_real[2]:.1f} prot={targets_real[3]:.1f}"
    )

    # Validator check
    validator = NutritionValidator()
    result = validator.validate(prediction)
    logger.info(f"  Validator: valid={result.valid} confidence={result.confidence:.2f}")
    if result.flags:
        for flag in result.flags:
            logger.warning(f"    ⚠️  {flag}")

    logger.info("\n  Smoke check: ✅ Pipeline is wired end-to-end correctly")
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Evaluate ensemble + smoke check")
    parser.add_argument("--config", default="configs/experiment/ensemble_5fold.yaml")
    parser.add_argument(
        "--stage",
        choices=["all", "eval", "smoke"],
        default="all",
        help="Which stage to run (default: all)",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    if args.stage in ("all", "eval"):
        stage_evaluate(config)

    if args.stage in ("all", "smoke"):
        stage_smoke(config)


if __name__ == "__main__":
    main()
