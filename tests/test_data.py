"""Tests for NutriSnap data preprocessing and augmentation."""
import numpy as np
import pytest

from nutrisnap.data.preprocessing import (
    preprocess_rgb,
    preprocess_depth,
    resize_with_letterbox,
    apply_mask,
    normalize_for_model,
)
from nutrisnap.data.augmentation import get_augmentation_pipeline


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

    def test_not_identity(self):
        """preprocess_rgb actually modifies the image (not a no-op)."""
        img = np.random.randint(50, 200, (100, 100, 3), dtype=np.uint8)
        result = preprocess_rgb(img)
        # The preprocessing should change at least some pixel values
        assert not np.array_equal(result, img)


class TestPreprocessDepth:
    """Tests for depth map preprocessing."""

    def test_output_range_01(self):
        """preprocess_depth normalizes to [0, 1] range."""
        # Simulate 16-bit depth (values in mm)
        depth = np.random.randint(0, 30000, (100, 100), dtype=np.uint16)
        result = preprocess_depth(depth)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_output_dtype_float32(self):
        """preprocess_depth returns float32."""
        depth = np.random.randint(0, 30000, (100, 100), dtype=np.uint16)
        result = preprocess_depth(depth)
        assert result.dtype == np.float32

    def test_zero_depth_stays_zero(self):
        """Zero depth maps produce zero output."""
        depth = np.zeros((100, 100), dtype=np.uint16)
        result = preprocess_depth(depth)
        assert np.allclose(result, 0.0)


class TestResizeWithLetterbox:
    """Tests for aspect-ratio-safe letterboxing."""

    def test_output_target_size(self):
        """resize_with_letterbox produces exact target dimensions."""
        img = np.random.randint(0, 255, (300, 200, 3), dtype=np.uint8)
        result = resize_with_letterbox(img, target_size=(224, 224))
        assert result.shape == (224, 224, 3)

    def test_no_stretching(self):
        """Non-square input should have padding (not stretching)."""
        img = np.ones((100, 200, 3), dtype=np.uint8) * 128
        result = resize_with_letterbox(img, target_size=(224, 224), fill_value=(0, 0, 0))
        # Top and bottom should have padding (zeros)
        assert result[0, 112, 0] == 0  # top center should be padding

    def test_single_channel(self):
        """resize_with_letterbox works on single-channel images."""
        img = np.random.randint(0, 255, (300, 200), dtype=np.uint8)
        result = resize_with_letterbox(img, target_size=(224, 224))
        assert result.shape == (224, 224)


class TestApplyMask:
    """Tests for mask application."""

    def test_background_zeroed(self):
        """apply_mask zeros out background pixels."""
        img = np.ones((100, 100, 3), dtype=np.uint8) * 200
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:80, 20:80] = 255  # food region in center
        result = apply_mask(img, mask)
        # Background should be zero
        assert result[0, 0, 0] == 0
        # Food region should be preserved
        assert result[50, 50, 0] == 200


class TestNormalizeForModel:
    """Tests for ImageNet normalization."""

    def test_output_float32(self):
        """normalize_for_model returns float32."""
        img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = normalize_for_model(img)
        assert result.dtype == np.float32

    def test_output_centered(self):
        """Mean of normalized ImageNet-like image should be near zero."""
        img = np.full((224, 224, 3), 124, dtype=np.uint8)  # ~0.486, close to ImageNet mean
        result = normalize_for_model(img)
        assert abs(result[:, :, 0].mean()) < 0.5  # roughly centered


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
        img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        mask = np.ones((300, 300), dtype=np.uint8) * 255
        r1 = pipeline(image=img, mask=mask)
        r2 = pipeline(image=img, mask=mask)
        assert np.array_equal(r1["image"], r2["image"])

    def test_mask_and_image_same_spatial_shape(self):
        """Augmented image and mask must have same (H, W)."""
        pipeline = get_augmentation_pipeline("train", target_size=(224, 224))
        img = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
        mask = np.ones((300, 400), dtype=np.uint8) * 255
        result = pipeline(image=img, mask=mask)
        assert result["image"].shape[:2] == result["mask"].shape[:2]

    def test_invalid_mode_raises(self):
        """Invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown augmentation mode"):
            get_augmentation_pipeline("invalid")

    def test_depth_additional_target(self):
        """Pipeline supports 'depth' as additional target."""
        pipeline = get_augmentation_pipeline("val", target_size=(224, 224), normalize=False)
        img = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        depth = np.random.randint(0, 255, (300, 300), dtype=np.uint8) # Fixed depth shape
        mask = np.ones((300, 300), dtype=np.uint8) * 255
        # Albumentations usually expects (H, W) or (H, W, C) for additional targets.
        # If 'depth' is 'image', it expects (H, W) or (H, W, C).
        result = pipeline(image=img, mask=mask, depth=depth)
        assert result["depth"].shape[:2] == (224, 224)


class TestGenerateRGBD:
    """Tests for RGBD artifact generation."""

    def test_generate_rgbd_shape(self, tmp_path):
        """generate_rgbd produces (4, 224, 224) tensor."""
        # Create a small test image
        test_img = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
        rgb_path = tmp_path / "test_rgb.png"
        import cv2

        cv2.imwrite(str(rgb_path), cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR))

        from nutrisnap.data.preprocessing import _DEFAULT_CONFIG
        import sys
        from pathlib import Path

        sys_path_addition = str(Path("j:/NutriSnap/scripts"))
        if sys_path_addition not in sys.path:
            sys.path.insert(0, sys_path_addition)

        try:
            from generate_rgbd_artifacts import generate_rgbd
            rgbd = generate_rgbd(rgb_path, None, _DEFAULT_CONFIG, target_size=(224, 224))
            assert rgbd.shape == (4, 224, 224)
            assert rgbd.dtype == np.float32
        finally:
            if sys_path_addition in sys.path:
                sys.path.remove(sys_path_addition)

    def test_generate_rgbd_no_nan(self, tmp_path):
        """generate_rgbd output contains no NaN values."""
        test_img = np.random.randint(50, 200, (224, 224, 3), dtype=np.uint8)
        rgb_path = tmp_path / "test_rgb.png"
        import cv2

        cv2.imwrite(str(rgb_path), cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR))

        from nutrisnap.data.preprocessing import _DEFAULT_CONFIG
        import sys
        from pathlib import Path

        sys_path_addition = str(Path("j:/NutriSnap/scripts"))
        if sys_path_addition not in sys.path:
            sys.path.insert(0, sys_path_addition)

        try:
            from generate_rgbd_artifacts import generate_rgbd
            rgbd = generate_rgbd(rgb_path, None, _DEFAULT_CONFIG, target_size=(224, 224))
            assert not np.isnan(rgbd).any()
        finally:
            if sys_path_addition in sys.path:
                sys.path.remove(sys_path_addition)


class TestSmokeCheck:
    """Tests for the smoke check validation functions."""

    def test_check_artifact_valid(self, tmp_path):
        """check_artifact passes for valid RGBD artifact."""
        # Create valid artifact: (4, 224, 224) float32
        valid = np.random.randn(4, 224, 224).astype(np.float32)
        valid[3] = np.clip(valid[3], 0, 1)  # depth in [0, 1]
        valid[:3] = np.clip(valid[:3], -3, 3)  # RGB in normalized range

        npy_path = tmp_path / "valid.npy"
        np.save(str(npy_path), valid)

        import sys
        from pathlib import Path

        sys_path_addition = str(Path("j:/NutriSnap/scripts"))
        if sys_path_addition not in sys.path:
            sys.path.insert(0, sys_path_addition)

        try:
            from smoke_check_pipeline import check_artifact
            errors = check_artifact(npy_path)
            assert len(errors) == 0
        finally:
            if sys_path_addition in sys.path:
                sys.path.remove(sys_path_addition)

    def test_check_artifact_wrong_shape(self, tmp_path):
        """check_artifact detects wrong shape."""
        bad = np.random.randn(3, 224, 224).astype(np.float32)
        npy_path = tmp_path / "bad_shape.npy"
        np.save(str(npy_path), bad)

        import sys
        from pathlib import Path

        sys_path_addition = str(Path("j:/NutriSnap/scripts"))
        if sys_path_addition not in sys.path:
            sys.path.insert(0, sys_path_addition)

        try:
            from smoke_check_pipeline import check_artifact
            errors = check_artifact(npy_path)
            assert any("Shape mismatch" in e for e in errors)
        finally:
            if sys_path_addition in sys.path:
                sys.path.remove(sys_path_addition)

    def test_check_artifact_nan(self, tmp_path):
        """check_artifact detects NaN values."""
        bad = np.full((4, 224, 224), np.nan, dtype=np.float32)
        npy_path = tmp_path / "nan.npy"
        np.save(str(npy_path), bad)

        import sys
        from pathlib import Path

        sys_path_addition = str(Path("j:/NutriSnap/scripts"))
        if sys_path_addition not in sys.path:
            sys.path.insert(0, sys_path_addition)

        try:
            from smoke_check_pipeline import check_artifact
            errors = check_artifact(npy_path)
            assert any("NaN" in e for e in errors)
        finally:
            if sys_path_addition in sys.path:
                sys.path.remove(sys_path_addition)


class TestNutriSnapDataset:
    """Tests for NutriSnapDataset class."""

    def test_dataset_import(self):
        """NutriSnapDataset is importable."""
        from nutrisnap.data.dataset import NutriSnapDataset

        assert NutriSnapDataset is not None

    def test_collate_fn_import(self):
        """collate_fn is importable."""
        from nutrisnap.data.dataset import collate_fn

        assert collate_fn is not None

    def test_dataset_loads_samples(self, tmp_path):
        """Dataset loads RGBD samples from a split file."""
        # Create artifact dir
        rgbd_dir = tmp_path / "rgbd"
        rgbd_dir.mkdir()

        # Create 3 sample artifacts
        for i in range(3):
            dish_id = f"dish_{1000+i}"
            arr = np.random.randn(4, 224, 224).astype(np.float32)
            np.save(str(rgbd_dir / f"{dish_id}.npy"), arr)

        # Create split file
        split_file = tmp_path / "test_ids.txt"
        split_file.write_text("dish_1000\ndish_1001\ndish_1002\n")

        from nutrisnap.data.dataset import NutriSnapDataset

        ds = NutriSnapDataset(rgbd_dir=rgbd_dir, split_file=split_file)
        assert len(ds) == 3

        sample = ds[0]
        assert "rgbd" in sample
        assert "targets" in sample
        assert "dish_id" in sample
        assert sample["rgbd"].shape == (4, 224, 224)
        assert sample["targets"].shape == (4,)
