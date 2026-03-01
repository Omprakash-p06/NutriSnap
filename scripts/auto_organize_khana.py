"""Auto-organize Khana Dataset.

Automatically extracts and organizes the Khana dataset into our 4 classes:
rice, dal, paneer, roti.

Filters to only include images matching our target categories.
"""

import os
import shutil
import tarfile
from pathlib import Path
from typing import Dict, List, Set


# Target classes and their matching keywords
CLASS_KEYWORDS = {
    "rice": {
        "rice", "chawal", "biryani", "pulao", "pulav", "khichdi", 
        "fried rice", "jeera rice", "lemon rice", "curd rice",
        "veg biryani", "chicken biryani", "mutton biryani"
    },
    "dal": {
        "dal", "daal", "dhal", "lentil", "sambar", "sambhar",
        "dal makhani", "dal tadka", "dal fry", "chana dal",
        "toor dal", "masoor dal", "moong dal", "urad dal"
    },
    "paneer": {
        "paneer", "cottage cheese", "kadai paneer", "matar paneer",
        "palak paneer", "shahi paneer", "paneer butter masala",
        "paneer tikka", "paneer bhurji"
    },
    "roti": {
        "roti", "chapati", "chapatti", "phulka", "naan", "paratha",
        "parantha", "kulcha", "tandoori roti", "rumali roti",
        "missi roti", "laccha paratha"
    },
}

# Images per class target
IMAGES_PER_CLASS = 100


def load_labels(labels_path: str) -> Dict[str, str]:
    """Load labels mapping from file.
    
    Args:
        labels_path: Path to labels.txt
        
    Returns:
        Dictionary mapping image filename to label
    """
    labels = {}
    
    if not os.path.exists(labels_path):
        print(f"⚠ Labels file not found: {labels_path}")
        return labels
    
    with open(labels_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                filename = parts[0]
                label = " ".join(parts[1:]).lower()
                labels[filename] = label
    
    print(f"✓ Loaded {len(labels)} labels")
    return labels


def load_taxonomy(taxonomy_path: str) -> Dict[str, str]:
    """Load taxonomy mapping from CSV.
    
    Args:
        taxonomy_path: Path to taxonomy.csv
        
    Returns:
        Dictionary mapping class id to name
    """
    taxonomy = {}
    
    if not os.path.exists(taxonomy_path):
        print(f"⚠ Taxonomy file not found: {taxonomy_path}")
        return taxonomy
    
    with open(taxonomy_path, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                class_id = parts[0].strip()
                class_name = parts[1].strip().lower()
                taxonomy[class_id] = class_name
    
    print(f"✓ Loaded {len(taxonomy)} taxonomy entries")
    return taxonomy


def classify_image(label: str) -> str:
    """Classify an image based on its label.
    
    Args:
        label: Image label from labels.txt
        
    Returns:
        Target class name or None if no match
    """
    label_lower = label.lower()
    
    for target_class, keywords in CLASS_KEYWORDS.items():
        for keyword in keywords:
            if keyword in label_lower:
                return target_class
    
    return None


def extract_tarfile(tar_path: str, output_dir: str) -> None:
    """Extract tar.gz file.
    
    Args:
        tar_path: Path to tar.gz file
        output_dir: Output directory
    """
    print(f"Extracting {tar_path}...")
    
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(output_dir)
    
    print(f"✓ Extracted to {output_dir}")


def organize_dataset(
    source_dir: str,
    output_dir: str,
    labels_path: str,
    max_per_class: int = IMAGES_PER_CLASS,
) -> Dict[str, int]:
    """Organize images into class folders.
    
    Args:
        source_dir: Directory with extracted images
        output_dir: Output directory (ml/data/raw)
        labels_path: Path to labels.txt
        max_per_class: Maximum images per class
        
    Returns:
        Dictionary with count per class
    """
    counts = {cls: 0 for cls in CLASS_KEYWORDS}
    
    # Create output directories
    output_path = Path(output_dir)
    for cls in CLASS_KEYWORDS:
        (output_path / cls).mkdir(parents=True, exist_ok=True)
    
    # Load labels
    labels = load_labels(labels_path)
    
    # Find all images
    source_path = Path(source_dir)
    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    
    images_found = 0
    images_classified = 0
    
    for img_file in source_path.rglob("*"):
        if img_file.suffix.lower() not in image_extensions:
            continue
        
        images_found += 1
        
        # Get label from labels dict or folder name
        label = labels.get(img_file.name, img_file.parent.name)
        
        # Classify
        target_class = classify_image(label)
        
        if target_class and counts[target_class] < max_per_class:
            # Copy image
            new_name = f"{target_class}_{counts[target_class]:04d}{img_file.suffix}"
            dest = output_path / target_class / new_name
            shutil.copy2(img_file, dest)
            counts[target_class] += 1
            images_classified += 1
    
    print(f"\n✓ Found {images_found} images, classified {images_classified}")
    return counts


def print_summary(counts: Dict[str, int]) -> None:
    """Print organization summary."""
    print("\n" + "=" * 50)
    print("DATASET ORGANIZATION SUMMARY")
    print("=" * 50)
    
    total = sum(counts.values())
    
    for cls, count in counts.items():
        status = "✓" if count >= 75 else "⚠"
        bar = "█" * (count // 5) + "░" * ((100 - count) // 5)
        print(f"{status} {cls:<8}: {bar} {count}/100")
    
    print(f"\nTotal: {total} images")
    
    if total >= 300:
        print("\n✓ SUCCESS! Dataset ready for annotation.")
        print("\nNext steps:")
        print("1. Annotate with Roboflow: https://roboflow.com")
        print("2. Export in YOLO format")
        print("3. Run: python scripts/organize_dataset.py")
        print("4. Train: python ml/train_yolo.py")
    else:
        print(f"\n⚠ Need {300 - total} more images for minimum training set")


def main():
    """Main organization workflow."""
    print("=" * 50)
    print("Khana Dataset Auto-Organizer")
    print("Target: 100 images per class (rice, dal, paneer, roti)")
    print("=" * 50)
    
    # Paths
    download_dir = Path("./ml/data/downloads/khana")
    tar_path = download_dir / "dataset.tar.gz"
    labels_path = download_dir / "labels.txt"
    extract_dir = download_dir / "extracted"
    output_dir = Path("./ml/data/raw")
    
    # Check if tar file exists
    if tar_path.exists():
        # Extract
        extract_dir.mkdir(parents=True, exist_ok=True)
        extract_tarfile(str(tar_path), str(extract_dir))
        source_dir = extract_dir
    else:
        # Already extracted or different structure
        source_dir = download_dir
    
    # Organize
    print("\nOrganizing images by class...")
    counts = organize_dataset(
        str(source_dir),
        str(output_dir),
        str(labels_path),
    )
    
    print_summary(counts)


if __name__ == "__main__":
    main()
