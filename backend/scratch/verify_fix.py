import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.dataset import NutriSnapDataset  # noqa: E402


def verify_dataset():
    features_dir = PROJECT_ROOT / "datasets/processed/features"
    # Use any available split file or just a dummy one if we can find one
    split_files = list((PROJECT_ROOT / "datasets/splits").glob("*.txt"))
    if not split_files:
        print("No split files found in datasets/splits")
        return

    split_file = split_files[0]
    metadata_csv = PROJECT_ROOT / "datasets/raw/archive (4)/dish_nutrition_values.csv"

    print(f"Loading dataset with split: {split_file.name}")
    print(f"Metadata CSV: {metadata_csv}")

    ds = NutriSnapDataset(
        features_dir=features_dir, split_file=split_file, metadata_csv=metadata_csv
    )

    if len(ds) == 0:
        print("Dataset is empty!")
        return

    print(f"Dataset size: {len(ds)}")

    # Check first 5 samples
    for i in range(min(5, len(ds))):
        sample = ds[i]
        targets = sample["targets"]
        dish_id = sample["dish_id"]
        # targets are normalized by TARGET_SCALES: [500.0, 50.0, 80.0, 50.0]
        from nutrisnap.data.dataset import TARGET_SCALES

        real_targets = targets * TARGET_SCALES
        print(f"Sample {i} (dish_id: {dish_id}):")
        print(f"  Normalized targets: {targets}")
        print(f"  Real targets:       {real_targets}")

        if torch.all(targets == 0):
            print("  WARNING: All targets are zero!")
        else:
            print("  SUCCESS: Targets are non-zero.")


if __name__ == "__main__":
    verify_dataset()
