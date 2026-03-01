"""Dataset Organization Script.

Organizes downloaded images into train/val/test splits.
Creates YOLO-compatible directory structure.
"""

import os
import random
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# Class definitions
CLASSES = ["rice", "dal", "paneer", "roti"]

# Split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


def count_images(data_dir: str) -> Dict[str, int]:
    """Count images per class.
    
    Args:
        data_dir: Directory containing class folders
        
    Returns:
        Dictionary with count per class
    """
    counts = {}
    data_path = Path(data_dir)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    
    for cls in CLASSES:
        cls_dir = data_path / cls
        if cls_dir.exists():
            count = sum(
                1 for f in cls_dir.iterdir()
                if f.suffix.lower() in image_extensions
            )
            counts[cls] = count
        else:
            counts[cls] = 0
    
    return counts


def create_yolo_structure(base_dir: str) -> None:
    """Create YOLO-compatible directory structure.
    
    Args:
        base_dir: Base output directory
    """
    base_path = Path(base_dir)
    
    for split in ["train", "val", "test"]:
        (base_path / split / "images").mkdir(parents=True, exist_ok=True)
        (base_path / split / "labels").mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created YOLO directory structure in {base_dir}")


def split_dataset(
    raw_dir: str,
    output_dir: str,
    seed: int = 42,
) -> Dict[str, Dict[str, int]]:
    """Split dataset into train/val/test.
    
    Args:
        raw_dir: Directory with raw images (class folders)
        output_dir: Output directory for split data
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with counts per split per class
    """
    random.seed(seed)
    
    raw_path = Path(raw_dir)
    output_path = Path(output_dir)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    
    stats = {"train": {}, "val": {}, "test": {}}
    
    for class_idx, cls in enumerate(CLASSES):
        cls_dir = raw_path / cls
        
        if not cls_dir.exists():
            print(f"⚠ Class folder not found: {cls_dir}")
            continue
        
        # Get all images
        images = [
            f for f in cls_dir.iterdir()
            if f.suffix.lower() in image_extensions
        ]
        
        if not images:
            print(f"⚠ No images found for class: {cls}")
            continue
        
        # Shuffle
        random.shuffle(images)
        
        # Calculate split indices
        n_total = len(images)
        n_train = int(n_total * TRAIN_RATIO)
        n_val = int(n_total * VAL_RATIO)
        
        splits = {
            "train": images[:n_train],
            "val": images[n_train:n_train + n_val],
            "test": images[n_train + n_val:],
        }
        
        # Copy files
        for split_name, split_images in splits.items():
            for img in split_images:
                # Copy image
                dest = output_path / split_name / "images" / img.name
                shutil.copy2(img, dest)
            
            stats[split_name][cls] = len(split_images)
        
        print(f"✓ {cls}: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")
    
    return stats


def generate_labels_yaml(output_dir: str) -> None:
    """Generate YOLO data.yaml file.
    
    Args:
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    
    yaml_content = f"""# NutriSnap Food Detection Dataset
path: {output_path.absolute()}
train: train/images
val: val/images
test: test/images

# Classes
nc: {len(CLASSES)}
names: {CLASSES}
"""
    
    yaml_path = output_path / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)
    
    print(f"✓ Generated {yaml_path}")


def print_summary(stats: Dict[str, Dict[str, int]]) -> None:
    """Print dataset summary."""
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    
    totals = {"train": 0, "val": 0, "test": 0}
    
    print(f"\n{'Class':<12} {'Train':<8} {'Val':<8} {'Test':<8}")
    print("-" * 40)
    
    for cls in CLASSES:
        train = stats["train"].get(cls, 0)
        val = stats["val"].get(cls, 0)
        test = stats["test"].get(cls, 0)
        
        print(f"{cls:<12} {train:<8} {val:<8} {test:<8}")
        
        totals["train"] += train
        totals["val"] += val
        totals["test"] += test
    
    print("-" * 40)
    print(f"{'TOTAL':<12} {totals['train']:<8} {totals['val']:<8} {totals['test']:<8}")
    
    grand_total = sum(totals.values())
    print(f"\nGrand Total: {grand_total} images")
    
    if grand_total < 300:
        print("\n⚠ WARNING: Need at least 300 images for effective training!")
        print("   Add more images to ml/data/raw/<class>/ folders")


def main():
    """Main organization workflow."""
    print("=" * 50)
    print("NutriSnap Dataset Organizer")
    print("=" * 50)
    
    raw_dir = "./ml/data/raw"
    output_dir = "./ml/data/processed"
    
    # Check raw directory
    print("\nChecking raw data...")
    counts = count_images(raw_dir)
    
    total = sum(counts.values())
    print(f"\nFound {total} images in {raw_dir}:")
    for cls, count in counts.items():
        status = "✓" if count >= 50 else "⚠"
        print(f"  {status} {cls}: {count}")
    
    if total == 0:
        print("\n✗ No images found!")
        print("  Please add images to ml/data/raw/<class>/ folders first.")
        print("  See ml/data/DOWNLOAD_GUIDE.md for instructions.")
        return
    
    # Create structure
    print("\nCreating output structure...")
    create_yolo_structure(output_dir)
    
    # Split dataset
    print("\nSplitting dataset...")
    stats = split_dataset(raw_dir, output_dir)
    
    # Generate YAML
    generate_labels_yaml(output_dir)
    
    # Summary
    print_summary(stats)
    
    print("\n" + "=" * 50)
    print("NEXT STEPS")
    print("=" * 50)
    print("1. Annotate images using Roboflow or CVAT")
    print("2. Export annotations in YOLO format")
    print("3. Place .txt files in corresponding labels/ folders")
    print("4. Run: python ml/train_yolo.py --data ml/data/processed/data.yaml")


if __name__ == "__main__":
    main()
