# Strategy Pivot: NutriSnap Expert MVP
**Date: April 16, 2026**

## Background
Processing the full Nutrition5k dataset (~5,000 dishes) on a 4GB VRAM GPU (RTX 3050) presents significant challenges in terms of time and memory. To ensure high accuracy and rapid iteration for the MVP, we are pivoting from a broad generalist model to a focused "Expert" model.

## Goal
Build a highly accurate prototype on **10 visually distinct dish types**. This validates the core methodology while fitting comfortably within the 4GB hardware envelope.

## Selected "Expert 10" Dishes
The following dishes have been selected for Visual Diversity and Balanced Nutrition Profiles:

1.  **dish_1561662216**: Balanced Pork with Rice and Greens
2.  **dish_1563379132**: Mexican Chilaquiles (Texture focus)
3.  **dish_1563207364**: Breakfast Medley (Yam/Grapes/Eggs)
4.  **dish_1550795690**: Simple Apple (Basics validation)
5.  **dish_1563216717**: Chicken Breast with Broccoli (High Protein)
6.  **dish_1563476551**: Salmon with Squash and Pasta (Fine-grained)
7.  **dish_1562963704**: Asian Pork Noodles with Bok Choy
8.  **dish_1562611680**: Pepperoni Pizza with Steak (Dense Calories)
9.  **dish_1564432238**: Mixed Pineapple Salad (Fruity/Veggie)
10. **dish_1563998323**: Roasted Chicken with Potatoes (Classic)

## Staged Processing Pipeline

### Stage 1: Offline Feature Extraction (CPU)
*   **Offline Preprocessing**: Raw imagery (RGB + Depth) is resized to 224x224 and normalized.
*   **Format**: Features are saved as PyTorch tensors (`.pt`) or NumPy files (`.npy`).
*   **Result**: Training loop bypasses all image processing, loading precomputed features directly into memory.

### Stage 2: Fast On-the-Fly Augmentation
*   **Library**: Utilize **Albumentations** for highly optimized geometric transforms (flips, rotations).
*   **Location**: Performed on-the-fly during data loading to minimize disk space.

### Stage 3: Optimized Model Training
*   **Precision**: Enable **Mixed Precision (FP16)** using `torch.cuda.amp` to halve VRAM usage.
*   **Memory Management**: 
    *   Set `pin_memory=True` in DataLoader.
    *   Use **Gradient Accumulation** (e.g., Batch 4, Accumulate over 8 steps) to simulate a batch size of 32.
*   **Frozen Backbone**: Freeze the EfficientNet backbone and train only the nutrition regression heads (up to 26x reduction in GPU load).

## Next Steps
1.  Configure `configs/data/expert_10.yaml`.
2.  Run `scripts/extract_offline_features.py` for the selected IDs.
3.  Execute training using precomputed features.
