"""Portion Model Training Script.

Train XGBoost regressor for portion size estimation.
"""

import os
from typing import List, Tuple

import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor


def create_synthetic_data(  # pylint: disable=too-many-locals
    n_samples: int = 500,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Create synthetic training data for portion estimation.

    Since we don't have real portion labels, this generates
    synthetic data based on realistic assumptions.

    Args:
        n_samples: Number of samples to generate.

    Returns:
        Tuple of (features, labels, class_names).
    """
    np.random.seed(42)

    # Feature columns: [area, aspect_ratio, relative_area, width, height, cx, cy, class_id,
    #                    mean_depth, max_depth, depth_std]
    features = []
    labels = []
    classes = []

    # Food class configurations (class_id, min_grams, max_grams)
    # class_id matches YOLO data.yaml order: dal=0, paneer=1, rice=2, roti=3
    food_configs = {
        "dal": (0, 100, 300),
        "paneer": (1, 40, 150),
        "rice": (2, 80, 250),
        "roti": (3, 25, 60),
    }

    for food_class, (class_id, min_g, max_g) in food_configs.items():
        for _ in range(n_samples // 4):
            # Random portion size
            portion = np.random.uniform(min_g, max_g)

            # Generate correlated features (larger portion = larger area)
            portion_normalized = (portion - min_g) / (max_g - min_g)

            # Base area scales with portion (stronger correlation)
            base_area = 15000 + portion_normalized * 50000
            area = base_area + np.random.normal(0, 2000)
            area = max(area, 5000)  # Ensure positive

            width = np.sqrt(area) * np.random.uniform(0.85, 1.15)
            height = area / width
            aspect_ratio = width / height

            # Relative area (image is 640x640 = 409600)
            relative_area = area / 409600

            # Random center position
            cx = np.random.uniform(0.2, 0.8)
            cy = np.random.uniform(0.2, 0.8)

            # Depth features — correlated with portion and food type
            # Depth values are normalized 0-1 (0=closest, 1=farthest)
            # Heaped food → higher depth contrast, flat food → low depth
            if food_class == "roti":
                # Roti is flat — minimal depth variation
                mean_depth = 0.3 + np.random.normal(0, 0.05)
                max_depth = mean_depth + np.random.uniform(0.02, 0.08)
                depth_std = np.random.uniform(0.01, 0.04)
            elif food_class == "rice":
                # Rice can be heaped — depth scales with portion
                mean_depth = (
                    0.35 + portion_normalized * 0.25 + np.random.normal(0, 0.05)
                )
                max_depth = (
                    mean_depth
                    + portion_normalized * 0.15
                    + np.random.uniform(0.05, 0.15)
                )
                depth_std = 0.05 + portion_normalized * 0.1 + np.random.normal(0, 0.02)
            elif food_class == "dal":
                # Dal in bowl — medium depth, increases with portion
                mean_depth = 0.4 + portion_normalized * 0.2 + np.random.normal(0, 0.04)
                max_depth = (
                    mean_depth + portion_normalized * 0.1 + np.random.uniform(0.03, 0.1)
                )
                depth_std = (
                    0.03 + portion_normalized * 0.06 + np.random.normal(0, 0.015)
                )
            else:  # paneer
                # Paneer pieces — depth depends on piece thickness
                mean_depth = 0.3 + portion_normalized * 0.2 + np.random.normal(0, 0.05)
                max_depth = mean_depth + np.random.uniform(0.05, 0.15)
                depth_std = 0.04 + portion_normalized * 0.05 + np.random.normal(0, 0.02)

            # Clamp depth values
            mean_depth = np.clip(mean_depth, 0.1, 0.9)
            max_depth = np.clip(max_depth, mean_depth, 1.0)
            depth_std = np.clip(depth_std, 0.01, 0.3)

            features.append(
                [
                    area,
                    aspect_ratio,
                    relative_area,
                    width,
                    height,
                    cx,
                    cy,
                    class_id,
                    mean_depth,
                    max_depth,
                    depth_std,
                ]
            )
            labels.append(portion)
            classes.append(food_class)

    return np.array(features), np.array(labels), classes


def train_portion_model(  # pylint: disable=too-many-locals
    output_path: str = "./ml/weights/portion_model.joblib",
    n_samples: int = 500,
) -> None:
    """Train XGBoost portion estimation model.

    Args:
        output_path: Path to save trained model.
        n_samples: Number of synthetic samples to generate.
    """
    print("Generating synthetic training data...")
    # pylint: disable=invalid-name, unused-variable
    X, y, _classes = create_synthetic_data(n_samples)

    print(f"Dataset size: {len(X)} samples")
    print(f"Feature shape: {X.shape}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")

    # Train XGBoost model
    print("Training XGBoost model...")
    model = XGBRegressor(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test)

    # Calculate MAPE
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))

    print("\nEvaluation Results:")
    print(f"  MAPE: {mape:.2f}%")
    print(f"  MAE: {mae:.2f}g")
    print(f"  RMSE: {rmse:.2f}g")

    # Save model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    print(f"\nModel saved to: {output_path}")

    # Feature importance
    print("\nFeature Importance:")
    feature_names = [
        "area",
        "aspect_ratio",
        "relative_area",
        "width",
        "height",
        "center_x",
        "center_y",
        "class_id",
        "mean_depth",
        "max_depth",
        "depth_std",
    ]
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"  {name}: {importance:.4f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train portion estimation model")
    parser.add_argument("--output", default="./ml/weights/portion_model.joblib")
    parser.add_argument("--samples", type=int, default=500)

    args = parser.parse_args()

    train_portion_model(output_path=args.output, n_samples=args.samples)
