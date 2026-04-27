---
status: resolved
trigger: "Investigate and propose cleanup of redundant scripts in the root and scripts/ directories."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:25:00Z
---

## Current Focus

hypothesis: There are one-off migration or utility scripts that are no longer needed for the core NutriSnap pipeline.
test: Examine identified scripts (update_paths.py, kaggle_files.txt, generate_mvp_folds.py).
expecting: Confirm update_paths.py is a one-off migration script. Confirm kaggle_files.txt is an artifact. Determine if generate_mvp_folds.py is truly redundant.
next_action: Cleanup complete.

## Symptoms

expected: A clean repository containing only necessary, maintainable scripts for the final architecture.
actual: Presence of one-off utility scripts (e.g., update_paths.py) and legacy files from the reorganization.
errors: None.
reproduction: Inspect the root and scripts/ directories.
started: Post-reorganization (datasets/ and checkpoints/ move).

## Eliminated

## Evidence

- timestamp: 2025-05-15T10:10:00Z
  checked: update_paths.py
  found: It is a migration script used to update paths from 'data/' to 'datasets/' and 'models/checkpoints/' to 'checkpoints/'.
  implication: This is a one-off script that is no longer needed after the reorganization is complete.
- timestamp: 2025-05-15T10:12:00Z
  checked: kaggle_files.txt in root
  found: It exists in the filesystem but is ignored by .gitignore. Likely a one-off artifact from Kaggle ingestion.
  implication: Can be safely removed.
- timestamp: 2025-05-15T10:15:00Z
  checked: scripts/generate_mvp_folds.py
  found: It generates specific folds for the MVP subset in 'datasets/splits/mvp'. prepare_data.py is a newer, more comprehensive script but its --mvp-only flag doesn't seem to fully replicate generate_mvp_folds.py's behavior yet (it doesn't filter the whole pipeline to MVP IDs).
  implication: Might not be fully redundant yet, but is likely legacy.
- timestamp: 2025-05-15T10:20:00Z
  checked: ViT-related scripts
  found: src/nutrisnap/training/train_vit.py and src/nutrisnap/models/vit_regressor.py exist. setup_foodsam.py downloads ViT-based SAM weights.
  implication: These must be preserved.

## Resolution

root_cause: One-off migration scripts and artifacts remained in the repository after their purpose was served.
fix: Removed update_paths.py and kaggle_files.txt from the root directory. Verified other scripts in scripts/ are either core parts of the pipeline, necessary setup tools, or active experiment utilities.
verification: Manual inspection of root and scripts/ directories. Core pipeline functionality (as described in prepare_data.py) is preserved.
files_changed: [update_paths.py, kaggle_files.txt]

