"""PyTorch Dataset for NutriSnap RGBD meal artifacts.

Loads pre-generated RGBD .npy artifacts (4, H, W) and their corresponding
nutrition labels from the Nutrition5k metadata.

Usage:
    from nutrisnap.data.dataset import NutriSnapDataset

    dataset = NutriSnapDataset(
        rgbd_dir="data/processed/rgbd",
        split_file="data/splits/train_ids.txt",
        metadata_csv="data/raw/.../dish_nutrition_values.csv",
        augmentation=get_augmentation_pipeline("train"),
    )
"""
import csv
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.data import Dataset

from nutrisnap.utils.logger import get_logger

logger = get_logger(__name__)

# Nutrition label columns in order
NUTRITION_TARGETS = ["total_calories", "total_fat", "total_carb", "total_protein"]


class NutriSnapDataset(Dataset):
    """Dataset that loads RGBD .npy artifacts and nutrition labels.

    Each sample returns:
        - rgbd: torch.Tensor of shape (4, H, W) — preprocessed RGBD
        - targets: torch.Tensor of shape (4,) — [calories, fat, carbs, protein]
        - dish_id: str — dish identifier
    """

    def __init__(
        self,
        rgbd_dir: str | Path,
        split_file: str | Path,
        metadata_csv: Optional[str | Path] = None,
        volume_features_csv: Optional[str | Path] = None,
        transform=None,
    ):
        """Initialize NutriSnapDataset.

        Args:
            rgbd_dir: Directory containing <dish_id>.npy RGBD artifacts.
            split_file: Text file with one dish_id per line.
            metadata_csv: CSV with dish_id and nutrition columns.
                          If None, returns dummy targets (for inference).
            transform: Optional Albumentations Compose to apply at load time.
                       Note: transforms operate on HWC images, so RGBD is
                       transposed before transform and back after.
        """
        self.rgbd_dir = Path(rgbd_dir)
        self.transform = transform

        # Load dish IDs from split file
        split_path = Path(split_file)
        if not split_path.exists():
            raise FileNotFoundError(f"Split file not found: {split_path}")
        all_ids = [line.strip() for line in split_path.read_text().splitlines() if line.strip()]

        # Filter to only IDs that have RGBD artifacts
        self.dish_ids = [
            did for did in all_ids
            if (self.rgbd_dir / f"{did}.npy").exists()
        ]
        skipped = len(all_ids) - len(self.dish_ids)
        if skipped > 0:
            logger.warning(f"Skipped {skipped} dishes without RGBD artifacts")
        logger.info(f"NutriSnapDataset: {len(self.dish_ids)} samples from {split_path.name}")

        # Load nutrition metadata
        self.nutrition = {}
        if metadata_csv is not None:
            self._load_metadata(Path(metadata_csv))

        # Load scalar volume features
        self.volume_features = {}
        if volume_features_csv is not None:
            self._load_volume_features(Path(volume_features_csv))

    def _load_metadata(self, csv_path: Path) -> None:
        """Load nutrition metadata from CSV."""
        if not csv_path.exists():
            logger.warning(f"Metadata CSV not found: {csv_path}")
            return

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                dish_id = row.get("dish_id", "")
                try:
                    self.nutrition[dish_id] = {
                        "total_calories": float(row.get("total_calories", 0)),
                        "total_fat": float(row.get("total_fat", 0)),
                        "total_carb": float(row.get("total_carb", 0)),
                        "total_protein": float(row.get("total_protein", 0)),
                    }
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping {dish_id}: {e}")

        logger.info(f"Loaded nutrition data for {len(self.nutrition)} dishes")

    def _load_volume_features(self, csv_path: Path) -> None:
        """Load volume/area features from CSV."""
        if not csv_path.exists():
            logger.warning(f"Volume features CSV not found: {csv_path}")
            return

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                dish_id = row.get("dish_id", "")
                try:
                    # [volume_cm3, area_cm2, confidence]
                    self.volume_features[dish_id] = [
                        float(row.get("volume_cm3", 0)),
                        float(row.get("area_cm2", 0)),
                        float(row.get("confidence", 0)),
                    ]
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping volume features for {dish_id}: {e}")

        logger.info(f"Loaded volume features for {len(self.volume_features)} dishes")

    def __len__(self) -> int:
        return len(self.dish_ids)

    def __getitem__(self, idx: int) -> dict:
        """Load a single RGBD sample.

        Returns:
            dict with keys:
                - "rgb": torch.Tensor (3, H, W)
                - "depth": torch.Tensor (1, H, W)
                - "label": torch.Tensor (4,) — [cal, fat, carb, protein]
                - "dish_id": str
        """
        dish_id = self.dish_ids[idx]
        npy_path = self.rgbd_dir / f"{dish_id}.npy"

        # Load RGBD: (4, H, W) float32
        rgbd = np.load(str(npy_path))

        # Apply transform if provided (Albumentations works on HWC)
        if self.transform is not None:
            # Transpose to HWC for augmentation
            rgb_hwc = np.transpose(rgbd[:3], (1, 2, 0))  # (H, W, 3)
            depth_hwc = np.transpose(rgbd[3:4], (1, 2, 0))  # (H, W, 1)
            # Expand depth to 3-channel for Albumentations compatibility
            depth_3ch = np.repeat(depth_hwc, 3, axis=2)

            # Create dummy mask (all ones — real mask applied during generation)
            mask = np.ones(rgb_hwc.shape[:2], dtype=np.uint8) * 255

            augmented = self.transform(image=rgb_hwc, mask=mask, depth=depth_3ch)
            rgb_aug = augmented["image"]  # (H, W, 3)
            depth_aug = augmented["depth"][:, :, 0:1]  # (H, W, 1)

            # Transpose back to CHW
            rgb_chw = np.transpose(rgb_aug, (2, 0, 1))  # (3, H, W)
            depth_chw = np.transpose(depth_aug, (2, 0, 1))  # (1, H, W)
            rgbd = np.concatenate([rgb_chw, depth_chw], axis=0)  # (4, H, W)

        # Split into RGB and Depth tensors
        rgb_tensor = torch.from_numpy(rgbd[:3].copy().astype(np.float32))
        depth_tensor = torch.from_numpy(rgbd[3:4].copy().astype(np.float32))

        # Get nutrition targets (rename to label)
        if dish_id in self.nutrition:
            label = torch.tensor(
                [self.nutrition[dish_id][k] for k in NUTRITION_TARGETS],
                dtype=torch.float32,
            )
        else:
            label = torch.zeros(len(NUTRITION_TARGETS), dtype=torch.float32)

        # Get volume features (optional, keep but return in dict)
        if dish_id in self.volume_features:
            scalar_features = torch.tensor(
                self.volume_features[dish_id], dtype=torch.float32
            )
        else:
            scalar_features = torch.zeros(3, dtype=torch.float32)

        return {
            "rgb": rgb_tensor,
            "depth": depth_tensor,
            "label": label,
            "scalar_features": scalar_features,
            "dish_id": dish_id,
        }


def collate_fn(batch: list[dict]) -> dict:
    """Custom collate function for NutriSnapDataset.

    Returns:
        dict with:
            - "rgb": torch.Tensor (B, 3, H, W)
            - "depth": torch.Tensor (B, 1, H, W)
            - "label": torch.Tensor (B, 4)
            - "dish_ids": list[str]
    """
    return {
        "rgb": torch.stack([b["rgb"] for b in batch]),
        "depth": torch.stack([b["depth"] for b in batch]),
        "label": torch.stack([b["label"] for b in batch]),
        "scalar_features": torch.stack([b["scalar_features"] for b in batch]),
        "dish_ids": [b["dish_id"] for b in batch],
    }
