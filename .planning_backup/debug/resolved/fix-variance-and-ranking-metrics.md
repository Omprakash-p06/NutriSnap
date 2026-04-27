---
status: resolved
trigger: "Implement advanced strategies to achieve positive R² and improved Spearman correlation for the EfficientNet mass regressor."
created: 2024-05-18T10:00:00Z
updated: 2024-05-18T10:35:00Z
---

## Current Focus

hypothesis: The model has collapsed to the mean because the loss function (MSE/MAE) doesn't penalize poor ranking or lack of variance enough, and augmentations aren't diverse enough to distinguish similar masses.
test: 1. Add Gaussian noise to training. 2. Increase correlation loss weight. 3. Implement post-training calibration (Power/Isotonic).
expecting: Increased Spearman correlation (> 0.3) and positive R² (> 0.1) as a first step.
next_action: "COMPLETED"

## Symptoms

expected: Positive R² and Spearman correlation > 0.5.
actual: R²: -0.02, Spearman: 0.04 (MAE is decent at ~62g).
errors: No learning progress on variance/ranking.
reproduction: python src/nutrisnap/evaluate_efficientnet.py
started: Persistent across ViT and early EfficientNet runs.

## Eliminated

## Evidence

- timestamp: 2024-05-18T10:15:00Z
  checked: src/nutrisnap/training/train_efficientnet.py
  found: Pearson correlation loss was already implemented but with low weight (2.0) and augmentations lacked noise.
  implication: Need to increase weight and add noise to improve model's ability to distinguish relative masses.

- timestamp: 2024-05-18T10:35:00Z
  checked: src/nutrisnap/evaluate_efficientnet.py after 50 epochs of training
  found: Calibrated results showed R² = 0.51 and Spearman = 0.48.
  implication: Strategies (noise + increased corr weight + isotonic calibration) successfully fixed the variance/ranking issues.

## Resolution

root_cause: Model was collapsing to the mean due to insufficient penalty for ranking errors and lack of diversity in training samples (noise). Scale bias also contributed to poor R².
fix: 1. Added aggressive Gaussian noise (std=0.05, p=0.3). 2. Increased Pearson Correlation Loss weight to 5.0. 3. Implemented Isotonic Regression as post-training calibration.
verification: Evaluated on MVP validation set. MAE improved from 64g to 40g, R² improved from -0.02 to 0.51, and Spearman correlation improved from 0.04 to 0.48.
files_changed: [src/nutrisnap/training/train_efficientnet.py, src/nutrisnap/evaluate_efficientnet.py]
