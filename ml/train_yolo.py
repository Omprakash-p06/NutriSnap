"""YOLOv8 Training Script.

Fine-tune YOLOv8-Nano on food detection dataset.
"""

from pathlib import Path

from ultralytics import YOLO


def train_yolo(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    data_yaml: str = "configs/yolo_train.yaml",
    epochs: int = 100,
    batch_size: int = 16,
    image_size: int = 640,
    model_name: str = "yolov8n.pt",
    output_dir: str = "./ml/weights/",
) -> None:
    """Train YOLOv8 model on food detection dataset.

    Args:
        data_yaml: Path to YOLO data configuration YAML.
        epochs: Number of training epochs.
        batch_size: Batch size for training.
        image_size: Input image size.
        model_name: Base model name (yolov8n.pt for nano).
        output_dir: Directory to save trained weights.
    """
    print(f"Loading base model: {model_name}")
    model = YOLO(model_name)

    print("Starting training...")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=image_size,
        patience=20,  # Early stopping patience
        save=True,
        project=output_dir,
        name="food_detection",
        exist_ok=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        augment=True,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.0,
    )

    # Copy best weights to target location
    best_weights = Path(output_dir) / "food_detection" / "weights" / "best.pt"
    final_path = Path(output_dir) / "yolov8_food.pt"

    if best_weights.exists():
        import shutil  # pylint: disable=import-outside-toplevel

        shutil.copy(best_weights, final_path)
        print(f"Best model saved to: {final_path}")

    print("Training complete!")
    print(f"Results: mAP50={results.results_dict.get('metrics/mAP50(B)', 0):.4f}")


def validate_model(
    model_path: str = "./ml/weights/yolov8_food.pt",
    data_yaml: str = "configs/yolo_train.yaml",
) -> None:
    """Validate trained YOLO model.

    Args:
        model_path: Path to trained model.
        data_yaml: Path to YOLO data configuration.
    """
    model = YOLO(model_path)

    results = model.val(data=data_yaml)

    print("Validation Results:")
    print(f"  mAP50: {results.results_dict.get('metrics/mAP50(B)', 0):.4f}")
    print(f"  mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 0):.4f}")
    print(f"  Precision: {results.results_dict.get('metrics/precision(B)', 0):.4f}")
    print(f"  Recall: {results.results_dict.get('metrics/recall(B)', 0):.4f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train YOLOv8 food detection model")
    parser.add_argument(
        "--data", default="configs/yolo_train.yaml", help="Data YAML path"
    )
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--validate", action="store_true", help="Run validation only")

    args = parser.parse_args()

    if args.validate:
        validate_model()
    else:
        train_yolo(
            data_yaml=args.data,
            epochs=args.epochs,
            batch_size=args.batch,
            image_size=args.imgsz,
        )
