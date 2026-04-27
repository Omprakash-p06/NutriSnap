---
status: investigating
trigger: "missing-alphashape-module"
created: 2025-05-15T12:00:00Z
updated: 2025-05-15T12:00:00Z
---

## Current Focus

hypothesis: The 'alphashape' package is imported in the pipeline's `__init__.py`, making it a hard dependency for any script using the pipeline, even if they don't use volume estimation.
test: Uninstall alphashape and run `preprocess_full.py`.
expecting: `ModuleNotFoundError: No module named 'alphashape'`.
next_action: Fix `src/nutrisnap/pipeline/__init__.py` to avoid eager import of `VolumeEstimator` or handle missing dependency.

## Symptoms

expected: Preprocessing runs successfully for the MVP dish subset.
actual: Script crashes with ModuleNotFoundError: No module named 'alphashape'.
errors: ModuleNotFoundError: No module named 'alphashape'
reproduction: python scripts/preprocess_full.py --ids-file data/splits/mvp_subset_ids.txt (from user's shell snippet)
started: Started today; user wants to train MVP.

## Eliminated

<!-- APPEND only - prevents re-investigating -->

## Evidence

- timestamp: 2025-05-15T12:10:00Z
  checked: pip show alphashape
  found: alphashape was installed in multiple environments.
  implication: The issue is environment-specific, but the dependency is forced by the codebase structure.
- timestamp: 2025-05-15T12:15:00Z
  checked: scripts/preprocess_full.py
  found: It imports FoodSegmenter from nutrisnap.pipeline.
  implication: This triggers the execution of src/nutrisnap/pipeline/__init__.py.
- timestamp: 2025-05-15T12:20:00Z
  checked: src/nutrisnap/pipeline/__init__.py
  found: It imports VolumeEstimator, which imports alphashape.
  implication: alphashape becomes a hard dependency for anything importing from nutrisnap.pipeline.
- timestamp: 2025-05-15T12:25:00Z
  checked: Reproduction after uninstalling alphashape.
  found: Script failed with the exact same ModuleNotFoundError reported by user.
  implication: Confirmed root cause.

## Resolution

root_cause: `alphashape` is imported in `src/nutrisnap/pipeline/__init__.py`, making it a hard dependency for the entire pipeline package.
fix:
verification:
files_changed: []
