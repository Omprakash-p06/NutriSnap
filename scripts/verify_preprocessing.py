import sys
from pathlib import Path
import cv2
import numpy as np

# Add src/ to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from nutrisnap.data.preprocessing import preprocess_depth, load_preprocessing_config

def verify():
    depth_path = PROJECT_ROOT / "data/raw/archive (4)/imagery/realsense_overhead/dish_1556572657/depth_raw.png"
    if not depth_path.exists():
        print(f"Error: Test file not found at {depth_path}")
        return

    print(f"Loading raw depth: {depth_path}")
    raw_depth = cv2.imread(str(depth_path), cv2.IMREAD_UNCHANGED)
    if raw_depth is None:
        print("Error: Could not read image.")
        return

    print(f"Raw shape: {raw_depth.shape}, dtype: {raw_depth.dtype}")
    print(f"Raw stats - Min: {raw_depth.min()}, Max: {raw_depth.max()}, Zeros: {(raw_depth == 0).sum()}")

    # Load config
    config = load_preprocessing_config()
    
    # Process
    print("\nRunning enhanced preprocessing pipeline...")
    processed = preprocess_depth(raw_depth, config=config)

    print(f"Processed shape: {processed.shape}, dtype: {processed.dtype}")
    print(f"Processed stats - Min: {processed.min():.4f}, Max: {processed.max():.4f}")
    print(f"Zeros after hole-filling: {(processed == 0).sum()}")
    
    # Check if hole filling worked (should have fewer zeros unless entire regions are out of range)
    # Actually, clip_range [0.0, 0.4] might zero out distant things.
    # But inpainting should fill small internal holes.
    
    if processed.min() >= 0.0 and processed.max() <= 1.0:
        print("\nSUCCESS: Output is normalized to [0, 1].")
    else:
        print(f"\nFAILURE: Output range is [{processed.min()}, {processed.max()}]")

if __name__ == "__main__":
    verify()
