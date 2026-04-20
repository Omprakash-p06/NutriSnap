# NutriSnap: Final Implementation Strategy (MVP v1.3)

> **Last updated:** 2026-04-20
> **Status:** Targets Achieved ✅

This document records the definitive NutriSnap MVP implementation which successfully reached performance targets on April 20, 2026.

---

## 🏆 The Winning Architecture: EfficientNet + Calibration

The implementation reached its goals by combining a data-efficient CNN backbone with post-hoc statistical calibration to handle the 254-sample dataset.

### 1. Three-Stage 3D-Aware Pipeline
1.  **🍽️ Segment (SAM 2)**: Uses `facebook/sam2-hiera-tiny` to isolate food from background noise.
2.  **📐 Depth (GLPN)**: Uses `vinvino02/glpn-nyu` to recover 3D structure from 2D images.
3.  **🧠 Regress (EfficientNetV2-B0)**: A 5-channel composite (RGB + Mask + Depth) plus an explicit **Convex Hull Volume scalar** is fed into an EfficientNetV2-B0 regressor.

### 2. Learning Strategy
- **Backbone**: EfficientNetV2-B0 (pivoted from ViT for better small-data performance).
- **Loss**: Hybrid MSE + **Pearson Correlation Loss (weight 5.0)** to prioritize ranking.
- **Augmentation**: Aggressive spatial transforms and **Gaussian Noise** to prevent overfitting.
- **Target Space**: `log1p(mass)` to stabilize variance.

### 3. Post-Training Calibration
We implemented **Isotonic Regression** to correct for the inherent scale bias in the deep learning model. This single step pushed the R² score from near-zero to over 0.40 and boosted Spearman correlation to 0.60.

---

## 🎯 Final Performance Metrics (MVP - 20 Dishes)

| Metric | Raw EfficientNet | **Calibrated EfficientNet** | Target | Status |
|---|---|---|---|---|
| **Mass MAE** | 59.64 g | **46.22 g** | ≤ 50 g | **PASSED** |
| **R² Score** | 0.0174 | **0.4314** | > 0.40 | **PASSED** |
| **Spearman ρ** | 0.4608 | **0.6047** | > 0.50 | **PASSED** |

---

## 🛠️ Execution Workflow

1.  **Data Prep**: `python scripts/prepare_data.py --mvp-only` (Generates splits for 20 dishes).
2.  **Preprocessing**: `python scripts/preprocess_full.py --mvp-only --sampling-rate 50` (SAM 2 + GLPN).
3.  **Volume extraction**: `python scripts/calculate_volume.py` (Convex Hull).
4.  **Training**: `python src/nutrisnap/training/train_efficientnet.py --epochs 100`.
5.  **Evaluation**: `python src/nutrisnap/evaluate_efficientnet.py` (Includes Isotonic Calibration).

---

## 🏁 Final Conclusion
The pivot to EfficientNetV2-B0 combined with aggressive correlation-aware loss and post-training calibration is the most robust path for NutriSnap. It directly addresses the portion size challenge through explicit volume estimation and handles small-dataset variance through statistical correction.
