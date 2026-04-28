"""Test IoU and redundancy checking."""

import numpy as np


def compute_iou(mask1, mask2):
    """Compute IoU."""
    intersection = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    if union == 0:
        return 0.0
    return float(intersection) / float(union)


# Create two overlapping masks
mask1 = np.zeros((100, 100), dtype=np.uint8)
mask2 = np.zeros((100, 100), dtype=np.uint8)

# Square masks
mask1[20:60, 20:60] = 1
mask2[40:80, 40:80] = 1

iou = compute_iou(mask1, mask2)
print(f"IoU between overlapping squares: {iou:.3f}")
assert 0.1 < iou < 0.5, f"Expected partial overlap, got {iou}"

# Non-overlapping masks
mask3 = np.zeros((100, 100), dtype=np.uint8)
mask4 = np.zeros((100, 100), dtype=np.uint8)

mask3[10:30, 10:30] = 1
mask4[70:90, 70:90] = 1

iou_disjoint = compute_iou(mask3, mask4)
print(f"IoU between disjoint masks: {iou_disjoint:.3f}")
assert iou_disjoint == 0.0, f"Expected no overlap, got {iou_disjoint}"

# Nearly identical masks
mask5 = np.zeros((100, 100), dtype=np.uint8)
mask6 = np.zeros((100, 100), dtype=np.uint8)

mask5[20:60, 20:60] = 1
mask6[20:60, 20:60] = 1  # Identical

iou_same = compute_iou(mask5, mask6)
print(f"IoU between identical masks: {iou_same:.3f}")
assert iou_same > 0.99, f"Expected ~1.0, got {iou_same}"


def adjust_for_overlap(items_volumes, iou_threshold=0.15):
    """Adjust volumes for overlapping items."""
    adjusted = []
    for i, vol in enumerate(items_volumes):
        max_iou = 0.3  # Simulated max IoU for test
        if max_iou > iou_threshold:
            # Reduce volume
            reduction = 1.0 - (max_iou * 0.5)
            new_vol = vol * reduction
            print(f"Item {i}: {vol:.1f} -> {new_vol:.1f} cm3 (IoU={max_iou:.2f})")
            adjusted.append(new_vol)
        else:
            adjusted.append(vol)
    return adjusted


# Test volume adjustment
volumes = [100.0, 150.0, 50.0]
adjusted = adjust_for_overlap(volumes)
print(f"Adjusted volumes: {adjusted}")

print("\nAll redundancy tests passed!")
