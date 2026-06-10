"""Train the PortionCorrector — XGBoost residual corrector for food mass estimation.

Two training modes:
  1. --mode=logs   : Train from real inference logs (CSV with predicted/actual mass)
  2. --mode=synth  : Generate synthetic residuals from food-density bias patterns

Mode 2 is the default and works without any historical data. It encodes known
biases of monocular-depth + density pipelines:
  - Dense foods (meat, cheese): tendency to over-estimate volume → over-predict mass
  - Flat/liquid foods: near-zero ConvexHull volume → under-predict mass
  - Leafy foods: large volume, very low density → wild mass swings
  - Small items (fruit, samosa): mask pixel ratio is tiny → noisy depth stats

Usage:
    # Synthetic mode (default, no data required)
    python -m nutrisnap.training.train_portion_corrector

    # From inference logs (requires a logs CSV)
    python -m nutrisnap.training.train_portion_corrector \\
        --mode=logs --logs=reports/inference_logs.csv

Output:
    models/portion_corrector.joblib
    reports/portion_corrector_metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

_FEATURE_COLUMNS = [
    "predicted_mass_g",
    "volume_cm3",
    "volume_type_enc",
    "depth_mean",
    "depth_std",
    "depth_skew",
    "depth_p25",
    "depth_p75",
    "mask_pixel_ratio",
]

# Known bias patterns for synthetic generation
# Each entry: (food_category, density_class, mass_bias_factor, depth_skew_typical)
#   mass_bias_factor > 1.0 means pipeline typically over-predicts
#   mass_bias_factor < 1.0 means pipeline typically under-predicts
_BIAS_PATTERNS = [
    # (label_prefix, volume_type, bias_factor, depth_mean_range, mask_ratio_range)
    ("dense_meat", "convex", 1.35, (0.35, 0.50), (0.10, 0.25)),
    ("dense_cheese", "convex", 1.28, (0.38, 0.52), (0.08, 0.20)),
    ("rice_starch", "convex", 0.92, (0.30, 0.45), (0.15, 0.35)),
    ("liquid_dal", "flat", 0.45, (0.40, 0.55), (0.20, 0.40)),
    ("liquid_sambar", "flat", 0.40, (0.42, 0.58), (0.18, 0.38)),
    ("leafy_salad", "concave", 0.70, (0.25, 0.40), (0.25, 0.45)),
    ("flat_roti", "flat", 0.85, (0.38, 0.50), (0.12, 0.28)),
    ("small_fruit", "convex", 1.10, (0.30, 0.48), (0.04, 0.12)),
    ("fried_samosa", "convex", 1.20, (0.32, 0.48), (0.06, 0.14)),
    ("mixed_biryani", "convex", 0.95, (0.28, 0.42), (0.25, 0.45)),
]


def _generate_synthetic(
    n_samples: int = 3000, seed: int = 42
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic (features, true_mass) pairs.

    Simulates the pipeline's behaviour for different food types and encodes
    known systematic biases so XGBoost can learn corrections.
    """
    rng = np.random.default_rng(seed)
    X_list, y_list = [], []

    samples_per_pattern = n_samples // len(_BIAS_PATTERNS)

    for label, vol_type, bias, depth_range, mask_range in _BIAS_PATTERNS:
        vol_enc = {"convex": 0, "flat": 1, "concave": 2}.get(vol_type, 0)

        for _ in range(samples_per_pattern):
            # Simulate a "true" mass between 30g–600g
            true_mass = float(rng.uniform(30, 600))

            # Pipeline's raw prediction has the category bias + noise
            noise_factor = float(rng.normal(1.0, 0.12))
            predicted_mass = true_mass * bias * noise_factor
            predicted_mass = max(5.0, predicted_mass)

            # Volume proportional to mass (with noise)
            volume_cm3 = predicted_mass * rng.uniform(0.6, 1.4)

            # Depth statistics drawn from category distribution
            d_mean = float(rng.uniform(*depth_range))
            d_std = float(rng.uniform(0.02, 0.15))
            d_skew = float(rng.normal(0.2 if vol_type == "convex" else -0.3, 0.4))
            d_p25 = max(0.0, d_mean - d_std * 0.7)
            d_p75 = min(1.0, d_mean + d_std * 0.7)
            mask_ratio = float(rng.uniform(*mask_range))

            row = [
                predicted_mass,
                volume_cm3,
                float(vol_enc),
                d_mean,
                d_std,
                d_skew,
                d_p25,
                d_p75,
                mask_ratio,
            ]
            X_list.append(row)
            y_list.append(true_mass)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)

    # Shuffle
    idx = rng.permutation(len(X))
    return X[idx], y[idx]


def _load_from_logs(logs_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Load training data from an inference log CSV.

    Expected columns: predicted_mass_g, true_mass_g, volume_cm3, volume_type,
                      depth_mean, depth_std, depth_skew, depth_p25, depth_p75,
                      mask_pixel_ratio
    """
    import pandas as pd  # noqa: PLC0415

    df = pd.read_csv(logs_path)
    required = {"predicted_mass_g", "true_mass_g"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Logs CSV missing required columns: {missing}")

    # Encode volume_type if present
    vol_enc_map = {"convex": 0, "flat": 1, "concave": 2, "simple": 0, "unknown": 0}
    if "volume_type" in df.columns:
        df["volume_type_enc"] = (
            df["volume_type"].map(vol_enc_map).fillna(0).astype(float)
        )
    else:
        df["volume_type_enc"] = 0.0

    # Fill missing depth stats with neutral defaults
    defaults = {
        "volume_cm3": df.get("predicted_mass_g", 0) * 1.0,
        "depth_mean": 0.5,
        "depth_std": 0.05,
        "depth_skew": 0.0,
        "depth_p25": 0.45,
        "depth_p75": 0.55,
        "mask_pixel_ratio": 0.15,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    X = df[_FEATURE_COLUMNS].values.astype(np.float32)
    y = df["true_mass_g"].values.astype(np.float32)
    return X, y


def train(
    X: np.ndarray,
    y: np.ndarray,
    output_path: Path,
    metrics_path: Path,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
    subsample: float = 0.8,
    seed: int = 42,
) -> dict:
    """Train XGBoost and save model + metrics."""
    try:
        from xgboost import XGBRegressor  # noqa: PLC0415
    except ImportError:
        logger.error("XGBoost not installed. Run: pip install xgboost")
        sys.exit(1)

    import joblib  # noqa: PLC0415
    from sklearn.metrics import mean_absolute_error, r2_score  # noqa: PLC0415
    from sklearn.model_selection import train_test_split  # noqa: PLC0415

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )

    model = XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=seed,
        n_jobs=-1,
        verbosity=0,
    )

    logger.info(f"Training XGBoost on {len(X_train)} samples...")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    # Evaluate
    y_pred_val = model.predict(X_val)

    # Baseline: no correction (raw predictions only)
    baseline_mae = float(
        mean_absolute_error(y_val, X_val[:, 0])
    )  # col 0 = predicted_mass_g
    corrected_mae = float(mean_absolute_error(y_val, y_pred_val))
    r2 = float(r2_score(y_val, y_pred_val))

    # Feature importances
    importances = dict(zip(_FEATURE_COLUMNS, model.feature_importances_.tolist()))

    metrics = {
        "baseline_mae_g": round(baseline_mae, 2),
        "corrected_mae_g": round(corrected_mae, 2),
        "mae_improvement_g": round(baseline_mae - corrected_mae, 2),
        "mae_improvement_pct": (
            round((1 - corrected_mae / baseline_mae) * 100, 1)
            if baseline_mae > 0
            else 0.0
        ),
        "r2_score": round(r2, 4),
        "val_samples": len(y_val),
        "feature_importances": importances,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logger.info(f"Model saved -> {output_path}")

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved -> {metrics_path}")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train the PortionCorrector XGBoost residual corrector."
    )
    parser.add_argument(
        "--mode",
        choices=["synth", "logs"],
        default="synth",
        help="Training data source: synth (default) or logs (requires --logs).",
    )
    parser.add_argument(
        "--logs",
        type=Path,
        default=None,
        help="Path to inference logs CSV (required when --mode=logs).",
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=3000,
        help="Number of synthetic samples to generate (--mode=synth only).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/portion_corrector.joblib"),
        help="Output path for the trained model.",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path("reports/portion_corrector_metrics.json"),
        help="Output path for training metrics JSON.",
    )
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.mode == "logs":
        if args.logs is None or not args.logs.exists():
            logger.error(f"--mode=logs requires --logs=<path>. Got: {args.logs}")
            sys.exit(1)
        logger.info(f"Loading inference logs from {args.logs}...")
        X, y = _load_from_logs(args.logs)
        logger.info(f"Loaded {len(X)} samples from logs.")
    else:
        logger.info(f"Generating {args.n_samples} synthetic training samples...")
        X, y = _generate_synthetic(n_samples=args.n_samples, seed=args.seed)
        logger.info(f"Generated {len(X)} synthetic samples.")

    metrics = train(
        X,
        y,
        output_path=args.output,
        metrics_path=args.metrics,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.lr,
        seed=args.seed,
    )

    print("\n=== PortionCorrector Training Results ===")
    print(f"  Baseline MAE (raw pipeline):   {metrics['baseline_mae_g']:.1f} g")
    print(f"  Corrected MAE (XGBoost):       {metrics['corrected_mae_g']:.1f} g")
    print(
        f"  Improvement:                   {metrics['mae_improvement_g']:.1f} g  ({metrics['mae_improvement_pct']:.1f}%)"
    )
    print(f"  R² score:                      {metrics['r2_score']:.4f}")
    print("\nTop features by importance:")
    sorted_feats = sorted(metrics["feature_importances"].items(), key=lambda x: -x[1])
    for feat, imp in sorted_feats[:5]:
        print(f"  {feat:<25} {imp:.4f}")
    print(f"\nModel: {args.output}")
    print(f"Metrics: {args.metrics}")


if __name__ == "__main__":
    main()
