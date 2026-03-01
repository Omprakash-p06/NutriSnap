"""Dataset Exploration and Analysis Script.

Analyze training dataset statistics and distributions.
"""

import os
from collections import Counter
from pathlib import Path
from typing import Dict

import cv2
import numpy as np


def analyze_images(data_dir: str = "./ml/data/raw/") -> Dict:
    """Analyze image statistics in dataset.

    Args:
        data_dir: Directory containing images.

    Returns:
        Dictionary with analysis results.
    """
    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = [
        f for f in Path(data_dir).glob("**/*") if f.suffix.lower() in image_extensions
    ]

    if not image_files:
        print(f"No images found in {data_dir}")
        return {}

    print(f"Found {len(image_files)} images\n")

    sizes = []
    aspect_ratios = []
    file_sizes = []
    channels = Counter()

    for img_path in image_files:
        # File size
        file_sizes.append(os.path.getsize(img_path) / 1024)  # KB

        # Image properties
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w, c = image.shape
        sizes.append((w, h))
        aspect_ratios.append(w / h)
        channels[c] += 1

    # Calculate statistics
    widths = [s[0] for s in sizes]
    heights = [s[1] for s in sizes]

    results = {
        "total_images": len(image_files),
        "width": {
            "min": min(widths),
            "max": max(widths),
            "mean": np.mean(widths),
            "std": np.std(widths),
        },
        "height": {
            "min": min(heights),
            "max": max(heights),
            "mean": np.mean(heights),
            "std": np.std(heights),
        },
        "aspect_ratio": {
            "min": min(aspect_ratios),
            "max": max(aspect_ratios),
            "mean": np.mean(aspect_ratios),
        },
        "file_size_kb": {
            "min": min(file_sizes),
            "max": max(file_sizes),
            "mean": np.mean(file_sizes),
        },
        "channels": dict(channels),
    }

    # Print summary
    print("=" * 50)
    print("DATASET ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"\nTotal Images: {results['total_images']}")
    print(f"\nImage Dimensions:")
    print(
        f"  Width:  min={results['width']['min']}, max={results['width']['max']}, mean={results['width']['mean']:.0f}"
    )
    print(
        f"  Height: min={results['height']['min']}, max={results['height']['max']}, mean={results['height']['mean']:.0f}"
    )
    print(f"\nAspect Ratio: mean={results['aspect_ratio']['mean']:.2f}")
    print(
        f"\nFile Size (KB): min={results['file_size_kb']['min']:.1f}, max={results['file_size_kb']['max']:.1f}, mean={results['file_size_kb']['mean']:.1f}"
    )
    print(f"\nChannels: {results['channels']}")

    return results


def analyze_annotations(
    annotations_dir: str = "./ml/data/annotations/",
) -> Dict:
    """Analyze YOLO annotation statistics.

    Args:
        annotations_dir: Directory containing annotation files.

    Returns:
        Dictionary with annotation statistics.
    """
    annotation_files = list(Path(annotations_dir).glob("*.txt"))

    if not annotation_files:
        print(f"No annotation files found in {annotations_dir}")
        return {}

    print(f"\nFound {len(annotation_files)} annotation files")

    class_counts = Counter()
    boxes_per_image = []
    box_sizes = []

    for ann_path in annotation_files:
        with open(ann_path, "r") as f:
            lines = f.readlines()

        boxes_per_image.append(len(lines))

        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                w, h = float(parts[3]), float(parts[4])

                class_counts[class_id] += 1
                box_sizes.append((w, h))

    # Map class IDs to names
    class_names = {0: "rice", 1: "dal", 2: "paneer", 3: "roti"}

    results = {
        "total_annotations": sum(class_counts.values()),
        "images_with_annotations": len(annotation_files),
        "class_distribution": {
            class_names.get(k, f"class_{k}"): v for k, v in sorted(class_counts.items())
        },
        "boxes_per_image": {
            "min": min(boxes_per_image) if boxes_per_image else 0,
            "max": max(boxes_per_image) if boxes_per_image else 0,
            "mean": np.mean(boxes_per_image) if boxes_per_image else 0,
        },
    }

    print("\n" + "=" * 50)
    print("ANNOTATION ANALYSIS")
    print("=" * 50)
    print(f"\nTotal Bounding Boxes: {results['total_annotations']}")
    print(f"Images with Annotations: {results['images_with_annotations']}")
    print(f"\nClass Distribution:")
    for cls, count in results["class_distribution"].items():
        pct = (
            count / results["total_annotations"] * 100
            if results["total_annotations"] > 0
            else 0
        )
        print(f"  {cls}: {count} ({pct:.1f}%)")
    print(
        f"\nBoxes per Image: min={results['boxes_per_image']['min']}, max={results['boxes_per_image']['max']}, mean={results['boxes_per_image']['mean']:.1f}"
    )

    return results


def check_dataset_quality(data_dir: str = "./ml/data/raw/") -> None:
    """Check dataset for potential quality issues.

    Args:
        data_dir: Directory containing images.
    """
    print("\n" + "=" * 50)
    print("QUALITY CHECK")
    print("=" * 50)

    image_extensions = {".jpg", ".jpeg", ".png"}
    image_files = list(Path(data_dir).glob("**/*"))
    image_files = [f for f in image_files if f.suffix.lower() in image_extensions]

    issues = {
        "corrupt": [],
        "too_small": [],
        "too_large": [],
        "low_contrast": [],
    }

    for img_path in image_files:
        image = cv2.imread(str(img_path))

        # Check for corrupt images
        if image is None:
            issues["corrupt"].append(img_path.name)
            continue

        h, w = image.shape[:2]

        # Check size
        if w < 224 or h < 224:
            issues["too_small"].append(img_path.name)
        elif w > 4096 or h > 4096:
            issues["too_large"].append(img_path.name)

        # Check contrast (standard deviation of grayscale)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if np.std(gray) < 20:
            issues["low_contrast"].append(img_path.name)

    # Print issues
    print(f"\nCorrupt images: {len(issues['corrupt'])}")
    if issues["corrupt"]:
        print(f"  {issues['corrupt'][:5]}...")

    print(f"Too small (<224px): {len(issues['too_small'])}")
    print(f"Too large (>4096px): {len(issues['too_large'])}")
    print(f"Low contrast: {len(issues['low_contrast'])}")

    if not any(issues.values()):
        print("\n✓ No quality issues found!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Explore dataset")
    parser.add_argument("--data-dir", default="./ml/data/raw/", help="Data directory")
    parser.add_argument("--annotations-dir", default="./ml/data/annotations/")
    parser.add_argument("--quality", action="store_true", help="Run quality check")

    args = parser.parse_args()

    analyze_images(args.data_dir)
    analyze_annotations(args.annotations_dir)

    if args.quality:
        check_dataset_quality(args.data_dir)
