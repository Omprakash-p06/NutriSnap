---
status: investigating
trigger: "Investigate and fix negative R² issue by pivoting the 3-stage pipeline backbone from ViT to EfficientNetV2-B0."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:00:00Z
---

## Current Focus

hypothesis: EfficientNetV2-B0 is more suitable for the small MVP dataset than ViT, which requires more data to generalize.
test: Replace ViT backbone with EfficientNetV2-B0 in the mass regressor and retrain.
expecting: Improved R² and Spearman correlation.
next_action: Implement EfficientNetRegressor using timm's tf_efficientnetv2_b0.

## Symptoms

expected: Positive R² and Spearman correlation > 0.5.
actual: Negative R², Spearman correlation near zero (0.08).
errors: Poor convergence/learning on the small MVP subset.
reproduction: python src/nutrisnap/training/train_vit.py
started: Since implementation of the 3-stage SAM 2 -> GLPN -> ViT pipeline.

## Eliminated

## Evidence

- timestamp: 2026-04-20T13:37:00Z
  checked: src/nutrisnap/training/train_vit.py and src/nutrisnap/models/vit_regressor.py
  found: Current implementation uses ViT-base with most layers frozen. Initial run showed Spearman of ~0.69 on a very small val set (9 samples), but the objective states it's failing overall.
  implication: Need to proceed with the requested pivot to a more parameter-efficient backbone.
- timestamp: 2026-04-20T13:40:00Z
  checked: Available models in torchvision and timm
  found: torchvision doesn't have efficientnet_v2_b0, but timm has tf_efficientnetv2_b0.
  implication: Will use timm for the backbone.

root_cause:
fix:
verification:
files_changed: []
