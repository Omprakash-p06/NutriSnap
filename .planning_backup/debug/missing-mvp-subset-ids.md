---
status: investigating
trigger: "Investigate issue: missing-mvp-subset-ids"
created: 2026-04-20T14:00:00Z
updated: 2026-04-20T14:00:00Z
---

## Current Focus

hypothesis: The directory `data/splits/` was wiped out during the manual cleanup, and all split files are missing, including `mvp_subset_ids.txt`.
test: Run `scripts/prepare_data.py` to regenerate the split files.
expecting: Splits are regenerated and training can proceed.
next_action: Run `scripts/prepare_data.py`.

## Symptoms

expected: Training should start and load the dataset IDs.
actual: Script crashes with FileNotFoundError.
errors: ERROR | __main__ | IDs file not found: data/splits/mvp_subset_ids.txt
reproduction: python src/nutrisnap/training/train_efficientnet.py --epochs 100
started: Happened immediately after a manual data cleanup.

## Eliminated

## Evidence

- timestamp: 2026-04-20T14:05:00Z
  checked: Existence of `data/splits/mvp_subset_ids.txt`
  found: File is missing.
  implication: Confirmed the error message.
- timestamp: 2026-04-20T14:10:00Z
  checked: Contents of `data/splits/` directory.
  found: Directory is empty.
  implication: The entire splits directory was likely cleared, not just the MVP IDs.

## Resolution

root_cause:
fix:
verification:
files_changed: []
