"""Advanced regression diagnostics for NutriSnap Nutrition Estimation.

Generates Predicted vs. Actual and Residual plots, and reports trustworthiness metrics.
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from torch.utils.data import DataLoader
from tqdm import tqdm

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.dataset import NutriSnapDataset, collate_fn  # noqa: E402
from nutrisnap.pipeline.inference import NutritionPredictor  # noqa: E402
from nutrisnap.utils.logger import get_logger  # noqa: E402
from nutrisnap.utils.metrics import (  # noqa: E402
    binned_mae,
    calorie_mae,
    calorie_mape,
    prediction_bias,
    prediction_variance_ratio,
    r2_score,
    spearman_correlation,
)

logger = get_logger(__name__)


def plot_diagnostics(y_true, y_pred, output_dir: Path):
    """Generate and save diagnostic plots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # 1. Predicted vs Actual
    plt.figure(figsize=(10, 8))
    sns.regplot(
        x=y_pred, y=y_true, scatter_kws={"alpha": 0.4}, line_kws={"color": "red"}
    )
    plt.xlabel("Predicted Calories")
    plt.ylabel("Actual Calories")
    plt.title("Nutrition Estimation: Predicted vs. Actual")

    # Add identity line
    max_val = max(max(y_true), max(y_pred))
    plt.plot([0, max_val], [0, max_val], "--", color="gray", alpha=0.5)
    plt.savefig(output_dir / "pred_vs_actual.png")
    plt.close()

    # 2. Residuals
    plt.figure(figsize=(10, 8))
    residuals = y_true - y_pred
    sns.scatterplot(x=y_pred, y=residuals, alpha=0.4)
    plt.axhline(0, color="red", linestyle="--")
    plt.xlabel("Predicted Calories")
    plt.ylabel("Residuals (Actual - Predicted)")
    plt.title("Residual Diagnostic Plot")
    plt.savefig(output_dir / "residuals.png")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Nutrition Regression Diagnostics")
    parser.add_argument(
        "--checkpoint-dir", required=True, help="Directory containing fold checkpoints"
    )
    parser.add_argument("--model-config", default="configs/models/nutrition_v1.yaml")
    parser.add_argument(
        "--experiment-config", default="configs/experiment/baseline.yaml"
    )
    parser.add_argument(
        "--output-dir",
        default="reports/diagnostics",
        help="Output directory for reports",
    )
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Setup Predictor
    predictor = NutritionPredictor(
        checkpoint_dir=PROJECT_ROOT / args.checkpoint_dir,
        model_config_path=PROJECT_ROOT / args.model_config,
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
        volume_features_csv=PROJECT_ROOT / exp_cfg["volume_features_csv"],
    )

    test_loader = DataLoader(
        test_ds, batch_size=1, shuffle=False, num_workers=2, collate_fn=collate_fn
    )

    logger.info(f"Running diagnostics on {len(test_ds)} test samples...")

    all_preds_full = []
    all_targets_full = []

    for batch in tqdm(test_loader, desc="Running Inference"):
        rgbd = batch["rgbd"]
        scalars = batch["scalar_features"]
        targets = batch["targets"]

        res = predictor.predict(rgbd, scalars)
        all_preds_full.append(
            [res["calories"], res["fat"], res["carbs"], res["protein"]]
        )
        all_targets_full.append(targets.numpy()[0])

    preds_arr = np.array(all_preds_full)
    targets_arr = np.array(all_targets_full)

    # Focus on Calories for plots and primary diagnostics
    y_pred = preds_arr[:, 0]
    y_true = targets_arr[:, 0]

    # Metrics
    metrics = {
        "MAE": calorie_mae(y_true, y_pred),
        "MAPE": calorie_mape(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
        "Spearman": spearman_correlation(y_true, y_pred),
        "Bias": prediction_bias(y_true, y_pred),
        "VarRatio": prediction_variance_ratio(y_true, y_pred),
    }

    # Trustworthiness Status
    is_trustworthy = True
    reasons = []
    if metrics["VarRatio"] < 0.15:
        is_trustworthy = False
        reasons.append("Low prediction variance (Constant Prediction Failure)")
    if metrics["Spearman"] < 0.5:
        is_trustworthy = False
        reasons.append("Poor rank correlation (Model cannot sort calorie density)")

    # Print Report
    print("\n" + "=" * 50)
    print("NUTRITION DIAGNOSTICS REPORT")
    print("=" * 50)
    print(f"Status: {'✅ TRUSTWORTHY' if is_trustworthy else '❌ FAILED'}")
    if reasons:
        for r in reasons:
            print(f"  - {r}")

    print("\nMetrics:")
    for k, v in metrics.items():
        print(f"  {k:10}: {v:.4f}")

    print("\nBinned MAE:")
    bins = binned_mae(y_true, y_pred)
    for k, v in bins.items():
        val = f"{v:.2f}" if v is not None else "N/A"
        print(f"  {k:15}: {val}")
    print("=" * 50)

    # Save Plots
    plot_diagnostics(y_true, y_pred, output_dir)
    logger.info(f"Diagnostic plots saved to {output_dir}")


if __name__ == "__main__":
    main()
