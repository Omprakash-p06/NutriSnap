---
status: awaiting_human_verify
trigger: "Investigate issue: training-anomaly-zero-mae"
created: 2024-04-20T10:00:00Z
updated: 2024-04-20T10:00:00Z
---

## Current Focus

hypothesis: Column name mismatch in NutriSnapDataset._load_metadata causes target values to be zeroed out.
test: Update column names in dataset.py and verify targets are correctly loaded.
expecting: Realistic (non-zero) targets leading to realistic MAE.
next_action: archive session

## Symptoms

expected: Realistic MAE (40-80 kcal) and non-zero MAPE.
actual: MAE < 1 kcal, Loss ~0, MAPE 0.0%.
errors: Warning: Volume features CSV not found.
reproduction: python src/train.py --config configs/experiment/ensemble_mvp.yaml
started: Started with ensemble_mvp experiment.

## Eliminated

## Evidence

- timestamp: 2024-04-20T10:10:00Z
  checked: data/raw/archive (4)/dish_nutrition_values.csv
  found: Column names are `calories,fat,carb,protein` NOT `total_calories,total_fat,total_carb,total_protein`.
  implication: row.get() in _load_metadata returns 0 default for all targets.

- timestamp: 2024-04-20T10:12:00Z
  checked: src/nutrisnap/training/trainer.py MAPE calculation
  found: MAPE calculation masks targets <= 5.0. If all targets are 0, MAPE returns 0.0.
  implication: Explains why MAPE is exactly 0.0%.

- timestamp: 2024-04-20T10:15:00Z
  checked: scratch/verify_fix.py
  found: After fixing NutriSnapDataset._load_metadata, targets are correctly loaded as non-zero values (e.g. 103.3 kcal for dish_1556575558).
  implication: Root cause confirmed and fix verified at dataset level.

## Resolution

root_cause: NutriSnapDataset._load_metadata was using internal keys (total_calories, etc.) to fetch from the CSV DictReader, but the Nutrition5k CSV uses shorter names (calories, fat, etc.), resulting in all targets being defaulted to 0.0.
fix: Updated NutriSnapDataset._load_metadata to attempt both 'total_' prefixed and non-prefixed column names.
verification: Created scratch/verify_fix.py which successfully loads non-zero targets from the dataset.
files_changed: ["src/nutrisnap/data/dataset.py"]
