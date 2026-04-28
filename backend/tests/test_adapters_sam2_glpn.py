from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from nutrisnap.pipeline.depth import DepthEstimatorGLPN
from nutrisnap.pipeline.segmenter import FoodSegmenterSAM2


def get_vram_usage():
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / 1024**2  # MB
    return 0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_sam2_glpn_vram_and_functionality():
    # 1. Setup paths
    image_path = Path(
        "datasets/raw/archive (4)/imagery/realsense_overhead/dish_1556572657/rgb.png"
    )
    if not image_path.exists():
        pytest.skip(f"Sample image not found: {image_path}")

    print(f"\nInitial VRAM: {get_vram_usage():.2f} MB")

    # 2. Test SAM 2
    print("Loading SAM 2...")
    segmenter = FoodSegmenterSAM2(model_id="facebook/sam2-hiera-tiny")
    vram_after_sam2_load = get_vram_usage()
    print(f"VRAM after SAM 2 load: {vram_after_sam2_load:.2f} MB")

    # Assert VRAM < 4GB (4096 MB)
    assert vram_after_sam2_load < 4000

    print("Running SAM 2 segmentation...")
    result = segmenter.segment(image_path)

    assert "combined_mask" in result
    assert isinstance(result["combined_mask"], np.ndarray)
    assert result["combined_mask"].shape[:2] == (
        Image.open(image_path).size[1],
        Image.open(image_path).size[0],
    )
    print(f"SAM 2 complete. Found {len(result['masks'])} regions.")

    # 3. Test GLPN
    print("Loading GLPN...")
    depth_estimator = DepthEstimatorGLPN()
    vram_after_both_load = get_vram_usage()
    print(f"VRAM after both models load: {vram_after_both_load:.2f} MB")

    # Assert VRAM < 4GB
    assert vram_after_both_load < 4000

    print("Running GLPN depth estimation...")
    depth_map = depth_estimator.estimate(image_path)

    assert isinstance(depth_map, np.ndarray)
    assert depth_map.shape == result["combined_mask"].shape
    assert depth_map.dtype == np.float32
    assert depth_map.min() >= 0.0
    assert depth_map.max() <= 1.0
    print("GLPN complete.")

    final_vram = get_vram_usage()
    print(f"Final VRAM: {final_vram:.2f} MB")
    assert final_vram < 4000


if __name__ == "__main__":
    # If run directly, just execute the logic
    try:
        test_sam2_glpn_vram_and_functionality()
        print("\nSUCCESS: Both models verified within VRAM limits.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback

        traceback.print_exc()
