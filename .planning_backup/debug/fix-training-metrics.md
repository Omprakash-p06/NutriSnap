---
status: investigating
trigger: "Investigate and fix negative R² and zero Spearman correlation in ViT mass regressor training."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:00:00Z
---

## Current Focus

hypothesis: Data mismatch or improper normalization prevents ViT from learning.
test: Examine training logs and data loading logic.
expecting: Identify why Spearman is zero (no correlation) and R² is negative (worse than mean).
next_action: gather initial evidence

## Symptoms

expected: R² > 0.5, Spearman > 0.6, MAE decreasing significantly.
actual: Negative R², Zero Spearman, Loss/MAE plateauing at high values (115g+).
errors: Data mismatch warnings in logs: "Missing label or volume for dish...".
reproduction: python src/nutrisnap/training/train_vit.py --epochs 2
started: Observed immediately after implementing the 3-stage pipeline.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
