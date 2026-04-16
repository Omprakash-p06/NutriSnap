from pathlib import Path

import numpy as np
import torch


def verify_masking(pt_path):
    tensor = torch.load(pt_path)
    # tensor shape is (C, 224, 224)
    # We expect some 0.0 values where masking occurred.

    total_pixels = tensor.numel()
    zero_pixels = (tensor == 0.0).sum().item()
    zero_percent = (zero_pixels / total_pixels) * 100

    print(f"File: {Path(pt_path).name}")
    print(f"  Shape: {list(tensor.shape)}")
    print(f"  Zeros: {zero_pixels} ({zero_percent:.2f}%)")

    if zero_percent > 1.0:
        print("  [PASS] Masking detected (background zeroed).")
    else:
        print("  [FAIL] No significant masking detected.")


if __name__ == "__main__":
    features_dir = Path("data/processed/features")
    pt_files = sorted(list(features_dir.glob("*_rgb.pt")))
    if pt_files:
        verify_masking(pt_files[0])
    else:
        print("No .pt files found.")
