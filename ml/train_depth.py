"""Depth Model Training Script.

Fine-tune or prepare Depth Anything V2 for food depth estimation.
"""

import os
from pathlib import Path
import cv2
import numpy as np


def prepare_depth_data(
    image_dir: str = "./ml/data/processed/",
    output_dir: str = "./ml/data/depth_maps/",
) -> None:
    """Generate depth maps for training data using Depth Anything V2.

    Args:
        image_dir: Directory containing food images.
        output_dir: Directory to save depth maps.
    """
    try:
        from transformers import pipeline
    except ImportError:
        print("Error: transformers library not installed")
        print("Run: pip install transformers torch")
        return

    print("Loading Depth Anything V2 model...")
    depth_pipeline = pipeline(
        "depth-estimation",
        model="depth-anything/Depth-Anything-V2-Small-hf",
    )

    os.makedirs(output_dir, exist_ok=True)

    # Get all images
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        f for f in Path(image_dir).glob("*") if f.suffix.lower() in image_extensions
    ]

    print(f"Found {len(image_files)} images")

    for img_path in image_files:
        print(f"Processing: {img_path.name}")

        try:
            from PIL import Image

            image = Image.open(img_path)

            # Generate depth map
            result = depth_pipeline(image)
            depth_map = np.array(result["depth"])

            # Save depth map
            output_path = Path(output_dir) / f"{img_path.stem}_depth.npy"
            np.save(output_path, depth_map)

            # Also save as image for visualization
            depth_vis = (depth_map * 255).astype(np.uint8)
            vis_path = Path(output_dir) / f"{img_path.stem}_depth.png"
            cv2.imwrite(str(vis_path), depth_vis)

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"  Error: {e}")

    print(f"\nDepth maps saved to: {output_dir}")


def analyze_depth_features(
    depth_dir: str = "./ml/data/depth_maps/",
    annotations_path: str = "./ml/data/annotations/labels.json",
) -> None:
    """Analyze depth features for food regions.

    Args:
        depth_dir: Directory containing depth maps.
        annotations_path: Path to bounding box annotations.
    """
    import json

    # Load annotations
    if not os.path.exists(annotations_path):
        print(f"Annotations file not found: {annotations_path}")
        return

    with open(annotations_path, "r") as f:
        annotations = json.load(f)

    depth_features = []

    for annotation in annotations:
        image_name = annotation["image"]
        depth_path = Path(depth_dir) / f"{Path(image_name).stem}_depth.npy"

        if not depth_path.exists():
            continue

        depth_map = np.load(depth_path)

        for box in annotation.get("boxes", []):
            x1, y1, x2, y2 = box["bbox"]
            food_class = box["class"]

            # Extract depth region
            region = depth_map[int(y1) : int(y2), int(x1) : int(x2)]

            if region.size == 0:
                continue

            # Calculate depth features
            depth_features.append(
                {
                    "class": food_class,
                    "mean_depth": float(np.mean(region)),
                    "std_depth": float(np.std(region)),
                    "min_depth": float(np.min(region)),
                    "max_depth": float(np.max(region)),
                }
            )

    # Print summary
    print("Depth Feature Summary:")
    for food_class in ["rice", "dal", "paneer", "roti"]:
        class_features = [f for f in depth_features if f["class"] == food_class]
        if class_features:
            mean_depths = [f["mean_depth"] for f in class_features]
            print(f"  {food_class}: mean_depth={np.mean(mean_depths):.3f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Depth estimation processing")
    parser.add_argument("--generate", action="store_true", help="Generate depth maps")
    parser.add_argument("--analyze", action="store_true", help="Analyze depth features")
    parser.add_argument("--image-dir", default="./ml/data/processed/")
    parser.add_argument("--output-dir", default="./ml/data/depth_maps/")

    args = parser.parse_args()

    if args.generate:
        prepare_depth_data(args.image_dir, args.output_dir)
    elif args.analyze:
        analyze_depth_features(args.output_dir)
    else:
        print("Use --generate to create depth maps or --analyze to analyze features")
