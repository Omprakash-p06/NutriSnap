---
status: investigating
trigger: "Investigate issue: verify-results-failure-and-performance"
created: 2026-04-17T04:15:00Z
updated: 2026-04-17T20:10:00Z
---

## Current Focus

hypothesis: The model suffers from "neuron death" in the calorie and fat heads (Dying ReLU), resulting in 0.0 predictions in the smoke check. Training was also slightly unstable.
test: We have implemented Phase 1 (Leaky ReLU, Cosine Annealing, gradient clipping). Now running a 30-epoch training session to validate the fix.
expecting: Non-zero predictions in the smoke check and more stable gradients resulting in continuous learning.
next_action: Wait for training run to complete, then evaluate results.

## Symptoms

expected: Calorie MAE ≤ 40 kcal, MAPE ≤ 12%, R² ≥ 0.85, Spearman ≥ 0.90, Stage 2 smoke check completion with realistic predictions.
actual: 
  - Calorie MAE: 34.31 (TARGET MET)
  - R²: 0.777
  - MAPE: 112%
  - Spearman: 0.61
  - Smoke Check: Predicted cal=0.0, fat=0.0, prot=0.0 (Neuron death).
errors: None currently.
reproduction: Run `.venv\Scripts\python.exe scripts/verify_results.py --config configs/experiment/ensemble_mvp.yaml`.
started: 2026-04-17 04:07:28

## Eliminated

- hypothesis: val_ids.txt is missing.
  evidence: Fixed and verified.
- hypothesis: volume features are missing or unnormalized.
  evidence: Fixed (csv restored, SCALAR_SCALES implemented) and verified (MAE dropped to 34).

## Evidence

- timestamp: 2026-04-17T20:05:00Z
  checked: verify_results.py output
  found: Calorie MAE is 34.31, but smoke check predictions for cal/fat/prot are exactly 0.0.
  implication: The model is learning the mean accurately but the heads are collapsing/dying during training on the small MVP set.

## Resolution

root_cause: 1. Training was cut short (10 epochs) before Phase 3 (full backbone tuning) started. 2. Scalar features (volume, area) were unnormalized, with magnitudes up to 1500, causing imbalance in the fusion layer.
fix: Implemented `SCALAR_SCALES` in `NutriSnapDataset` to normalize volume (by 1000) and area (by 200) into a range ([0, 2]) consistent with RGB/Depth features.
verification: Verified normalization with `scratch/verify_normalization.py` (dish_1556575558 volume 1492 -> 1.492). 10-epoch test already showed MAE drop from 100 to 58 after restoring features; full training is now expected to reach < 40.
files_changed: [src/nutrisnap/data/dataset.py]
