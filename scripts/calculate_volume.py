import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.spatial import ConvexHull
from tqdm import tqdm


def estimate_volume(depth_map, pixel_to_mm_scale=1.0):
    """
    Estimates the 3D volume from a 2D depth map using a convex hull.
    Args:
        depth_map: 2D numpy array (H, W) in millimeters.
    Returns:
        float: Computed volume.
    """
    valid_depth = depth_map > 0

    # Get 3D coordinates
    H, W = depth_map.shape
    x, y = np.meshgrid(np.arange(W), np.arange(H))
    z = depth_map

    x = x * pixel_to_mm_scale
    y = y * pixel_to_mm_scale

    points = np.stack([x[valid_depth], y[valid_depth], z[valid_depth]], axis=-1)

    if len(points) < 4:
        return 0.0  # Not enough points for a 3D convex hull

    try:
        hull = ConvexHull(points)
        volume = hull.volume
    except Exception as e:
        # Fallback if hull fails (e.g. coplanar points)
        return 0.0

    return volume


def main():
    features_dir = Path("datasets/processed/features")
    output_csv = Path("datasets/processed/volumes.csv")

    if not features_dir.exists():
        print(f"Features directory not found: {features_dir}")
        return

    composite_files = list(features_dir.glob("*_composite.pt"))
    if not composite_files:
        print("No composite files found.")
        return

    results = []

    print(f"Calculating explicit volumes for {len(composite_files)} dishes...")

    for f in tqdm(composite_files):
        # Filename format: {dish_id}_{frame_idx}_composite.pt
        # The dish_id might contain underscores (e.g., dish_1556572657)
        # We find the dish_id by joining parts before the view name
        parts = f.stem.split("_")
        if "overhead" in f.stem:
            dish_id = "_".join(parts[: parts.index("overhead")])
        elif "camera" in f.stem:
            dish_id = "_".join(parts[: parts.index("camera")])
        else:
            dish_id = parts[0]  # Fallback

        # Load tensor: (5, 224, 224) -> RGB(3), Mask(1), Depth(1)
        pixel_values = torch.load(f, weights_only=True)

        # Depth map is channel index 4
        depth_tensor = pixel_values[4, :, :]
        # Mask is channel index 3
        mask_tensor = pixel_values[3, :, :]

        # INVERSION: Depth values in [0, 1] usually represent distance from camera.
        # Small values (0.1) are closer to camera (high food height).
        # Large values (0.9) are further (low food height).
        # Height should be (1.0 - depth) * mask
        height_map = (1.0 - depth_tensor.numpy()) * mask_tensor.numpy()

        # Scale to millimeters for the ConvexHull calculation
        # 1000 is an arbitrary scale factor to provide numerical stability
        height_map = height_map * 1000.0

        # Calculate volume using height_map
        vol = estimate_volume(height_map, pixel_to_mm_scale=2.0)

        results.append({"dish_id": dish_id, "filename": f.name, "volume": vol})

    df = pd.DataFrame(results)

    # Save the volumes
    df.to_csv(output_csv, index=False)
    print(f"Saved calculated volumes to {output_csv}")

    # Show stats
    print(df["volume"].describe())


if __name__ == "__main__":
    main()
