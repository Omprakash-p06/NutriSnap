"""Tests for NutriSnap data preprocessing and augmentation."""

import numpy as np
import pytest
import torch

from nutrisnap.data.augmentation import get_augmentation_pipeline
from nutrisnap.data.preprocessing import (
    preprocess_depth,
    preprocess_rgb,
    resize_with_letterbox,
)


class TestPreprocessRGB:
    """Tests for the RGB preprocessing pipeline."""

    def test_output_shape_preserved(self):
        """preprocess_rgb preserves HxWx3 shape."""
        img = np.random.randint(0, 255, (100, 150, 3), dtype=np.uint8)
        result = preprocess_rgb(img)
        assert result.shape == img.shape

    def test_output_dtype_uint8(self):
        """preprocess_rgb returns uint8."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = preprocess_rgb(img)
        assert result.dtype == np.uint8


class TestPreprocessDepth:
    """Tests for depth map preprocessing."""

    def test_output_range_01(self):
        """preprocess_depth normalizes to [0, 1] range."""
        depth = np.random.randint(0, 30000, (100, 100), dtype=np.uint16)
        result = preprocess_depth(depth)
        assert result.min() >= 0.0
        assert result.max() <= 1.0


class TestResizeWithLetterbox:
    """Tests for aspect-ratio-safe letterboxing."""

    def test_output_target_size(self):
        """resize_with_letterbox produces exact target dimensions."""
        img = np.random.randint(0, 255, (300, 200, 3), dtype=np.uint8)
        result = resize_with_letterbox(img, target_size=(224, 224))
        assert result.shape == (224, 224, 3)


class TestAugmentationPipeline:
    """Tests for Albumentations pipelines."""

    def test_train_pipeline_returns_compose(self):
        """get_augmentation_pipeline('train') returns Compose."""
        import albumentations as A

        pipeline = get_augmentation_pipeline("train")
        assert isinstance(pipeline, A.Compose)

    def test_val_deterministic(self):
        """Val pipeline should be deterministic (same input → same output)."""
        pipeline = get_augmentation_pipeline("val", target_size=(224, 224))
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        mask = np.ones((224, 224), dtype=np.uint8) * 255
        depth = np.random.randint(0, 255, (224, 224), dtype=np.uint8)
        r1 = pipeline(image=img, mask=mask, depth=depth)
        r2 = pipeline(image=img, mask=mask, depth=depth)
        assert np.array_equal(r1["image"], r2["image"])


class TestNutriSnapDataset:
    """Tests for NutriSnapDataset class."""

    @pytest.fixture
    def setup_artifacts(self, tmp_path):
        """Setup temporary artifacts for dataset testing."""
        features_dir = tmp_path / "features"
        features_dir.mkdir()

        # Create 2 sample artifacts: {dish_id}_{view}_rgb.pt
        for i in range(2):
            dish_id = f"dish_0{i+1}"
            view = "overhead"
            stem = f"{dish_id}_{view}"

            rgb = torch.randn(3, 224, 224)
            depth = torch.randn(1, 224, 224)

            torch.save(rgb, str(features_dir / f"{stem}_rgb.pt"))
            torch.save(depth, str(features_dir / f"{stem}_depth.pt"))

        split_file = tmp_path / "test_ids.txt"
        split_file.write_text("dish_01\ndish_02\n")

        # Metadata CSV
        metadata_csv = tmp_path / "metadata.csv"
        metadata_csv.write_text(
            "dish_id,total_calories,total_fat,total_carb,total_protein\ndish_01,500,20,50,15\n"
        )

        # Volume features CSV
        vol_csv = tmp_path / "volume_features.csv"
        vol_csv.write_text(
            "dish_id,volume_cm3,area_cm2,confidence\ndish_01,450.5,180.2,1.0\n"
        )

        return features_dir, split_file, metadata_csv, vol_csv

    def test_dataset_item_with_features(self, setup_artifacts):
        """Dataset returns scalar_features when provided."""
        features_dir, split_file, metadata_csv, vol_csv = setup_artifacts
        from nutrisnap.data.dataset import NutriSnapDataset

        ds = NutriSnapDataset(
            features_dir=features_dir,
            split_file=split_file,
            metadata_csv=metadata_csv,
            volume_features_csv=vol_csv,
        )

        assert len(ds) == 2
        sample = ds[0]

        assert "rgb" in sample
        assert "targets" in sample
        assert "scalar_features" in sample
        assert sample["rgb"].shape == (3, 224, 224)
        assert sample["targets"].shape == (4,)
        assert sample["scalar_features"].shape == (3,)

        # Verify values for dish_01
        assert sample["targets"][0] == 1.0  # 500 / 500 (TARGET_SCALES[0])
        assert sample["scalar_features"][0] == 0.4505  # 450.5 / 1000 (SCALAR_SCALES[0])
        assert sample["dish_id"] == "dish_01"

    def test_collate_fn(self, setup_artifacts):
        """collate_fn correctly batches samples including scalar features."""
        features_dir, split_file, metadata_csv, vol_csv = setup_artifacts
        from nutrisnap.data.dataset import NutriSnapDataset, collate_fn

        ds = NutriSnapDataset(
            features_dir=features_dir,
            split_file=split_file,
            volume_features_csv=vol_csv,
        )

        batch = [ds[0], ds[1]]
        collated = collate_fn(batch)

        assert collated["rgb"].shape == (2, 3, 224, 224)
        assert collated["targets"].shape == (2, 4)
        assert collated["scalar_features"].shape == (2, 3)
        assert len(collated["dish_ids"]) == 2
