"""Model Evaluation Script.

Evaluate trained models on test dataset.
"""

import json
from typing import Dict, Tuple

import numpy as np


def evaluate_yolo(
    model_path: str = "./ml/weights/yolov8_food.pt",
    data_yaml: str = "configs/yolo_train.yaml",
) -> Dict:
    """Evaluate YOLOv8 model on test set.

    Args:
        model_path: Path to trained model.
        data_yaml: Path to data configuration.

    Returns:
        Dictionary with evaluation metrics.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: ultralytics not installed")
        return {}

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    print("Running validation...")
    results = model.val(data=data_yaml, verbose=False)

    metrics = {
        "mAP50": float(results.results_dict.get("metrics/mAP50(B)", 0)),
        "mAP50-95": float(results.results_dict.get("metrics/mAP50-95(B)", 0)),
        "precision": float(results.results_dict.get("metrics/precision(B)", 0)),
        "recall": float(results.results_dict.get("metrics/recall(B)", 0)),
    }

    print("\n" + "=" * 50)
    print("YOLO EVALUATION RESULTS")
    print("=" * 50)
    print(f"  mAP@50:    {metrics['mAP50']:.4f}")
    print(f"  mAP@50-95: {metrics['mAP50-95']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")

    return metrics


def evaluate_portion_model(
    model_path: str = "./ml/weights/portion_model.joblib",
    test_data_path: str = "./ml/data/test_portions.json",
) -> Dict:
    """Evaluate portion estimation model.

    Args:
        model_path: Path to trained model.
        test_data_path: Path to test data JSON.

    Returns:
        Dictionary with evaluation metrics.
    """
    try:
        import joblib
    except ImportError:
        print("Error: joblib not installed")
        return {}

    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return {}

    print(f"Loading model: {model_path}")
    model = joblib.load(model_path)

    # Generate synthetic test data if file doesn't exist
    if not os.path.exists(test_data_path):
        print("Generating synthetic test data...")
        test_features, test_labels = _generate_test_data()
    else:
        with open(test_data_path, "r") as f:
            test_data = json.load(f)
        test_features = np.array(test_data["features"])
        test_labels = np.array(test_data["labels"])

    # Predict
    predictions = model.predict(test_features)

    # Calculate metrics
    mape = np.mean(np.abs((test_labels - predictions) / test_labels)) * 100
    mae = np.mean(np.abs(test_labels - predictions))
    rmse = np.sqrt(np.mean((test_labels - predictions) ** 2))

    metrics = {
        "MAPE": float(mape),
        "MAE": float(mae),
        "RMSE": float(rmse),
    }

    print("\n" + "=" * 50)
    print("PORTION MODEL EVALUATION RESULTS")
    print("=" * 50)
    print(f"  MAPE: {metrics['MAPE']:.2f}%")
    print(f"  MAE:  {metrics['MAE']:.2f}g")
    print(f"  RMSE: {metrics['RMSE']:.2f}g")

    # Check if target MAPE is met
    target_mape = 20.0
    if mape <= target_mape:
        print(f"\n✓ Target MAPE (≤{target_mape}%) ACHIEVED!")
    else:
        print(f"\n✗ Target MAPE (≤{target_mape}%) not met")

    return metrics


def _generate_test_data(n_samples: int = 100) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic test data.

    Args:
        n_samples: Number of test samples.

    Returns:
        Tuple of (features, labels).
    """
    np.random.seed(42)

    features = []
    labels = []

    for _ in range(n_samples):
        portion = np.random.uniform(30, 250)

        # Generate correlated features
        portion_normalized = (portion - 30) / 220
        area = 10000 + portion_normalized * 40000 + np.random.normal(0, 3000)
        width = np.sqrt(area) * np.random.uniform(0.8, 1.2)
        height = area / width
        aspect_ratio = width / height
        relative_area = area / 409600
        cx = np.random.uniform(0.2, 0.8)
        cy = np.random.uniform(0.2, 0.8)

        features.append([area, aspect_ratio, relative_area, width, height, cx, cy])
        labels.append(portion)

    return np.array(features), np.array(labels)


def generate_evaluation_report(
    output_path: str = "./ml/evaluation_report.json",
) -> None:
    """Generate comprehensive evaluation report.

    Args:
        output_path: Path to save report.
    """
    report = {
        "yolo": {},
        "portion": {},
        "overall": {},
    }

    # Evaluate YOLO if available
    if os.path.exists("./ml/weights/yolov8_food.pt"):
        report["yolo"] = evaluate_yolo()
    else:
        print("YOLO model not found, skipping...")

    # Evaluate portion model if available
    if os.path.exists("./ml/weights/portion_model.joblib"):
        report["portion"] = evaluate_portion_model()
    else:
        print("Portion model not found, skipping...")

    # Overall assessment
    yolo_pass = report["yolo"].get("mAP50", 0) >= 0.85
    portion_pass = report["portion"].get("MAPE", 100) <= 20

    report["overall"] = {
        "yolo_target_met": yolo_pass,
        "portion_target_met": portion_pass,
        "all_targets_met": yolo_pass and portion_pass,
    }

    # Save report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate models")
    parser.add_argument("--yolo", action="store_true", help="Evaluate YOLO")
    parser.add_argument("--portion", action="store_true", help="Evaluate portion model")
    parser.add_argument("--report", action="store_true", help="Generate full report")

    args = parser.parse_args()

    if args.yolo:
        evaluate_yolo()
    elif args.portion:
        evaluate_portion_model()
    elif args.report:
        generate_evaluation_report()
    else:
        # Default: generate full report
        generate_evaluation_report()
