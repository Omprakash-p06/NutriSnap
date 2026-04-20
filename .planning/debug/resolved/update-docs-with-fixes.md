---
status: investigating
trigger: "Investigate issue: update-docs-with-fixes. Summary: Iterate through the whole project one by one and update the final strategy file and README.md, give me the steps to prepare data, preprocess it, train it etc."
created: 2024-04-18T10:00:00Z
updated: 2024-04-18T10:00:00Z
---

## Current Focus

hypothesis: Documentation is outdated regarding SAM setup, CUDA, training anomalies, and the overall pipeline flow.
test: Compare debug reports and codebase with README.md and the strategy file.
expecting: Discrepancies between documentation and actual project state.
next_action: gather initial evidence by reading debug files and existing docs.

## Symptoms

expected: Documentation (README and Strategy file) should accurately reflect the current state of the project, including all recent fixes and the correct sequence of steps for data preparation, preprocessing, and training.
actual: Documentation is likely out of sync with recent debug findings (e.g., SAM setup, CUDA, training anomalies) and needs to be updated to match the latest codebase state.
errors: None (documentation gap).
reproduction: Compare the README.md and the final strategy file with the latest code and the debug reports in .planning/debug/.
started: Post-debug sessions.

## Eliminated

## Evidence

- timestamp: 2024-04-18T22:30:00Z
  checked: .planning/debug/ files
  found: Recent fixes include:
    1. SAM weight corruption + CUDA fallback fixed (scripts/setup_foodsam.py).
    2. Column name mismatch in NutriSnapDataset (calories vs total_calories) fixed.
    3. SCALAR_SCALES normalization for volume (1000) and area (200) added to NutriSnapDataset.
    4. Dying ReLU issue addressed with Leaky ReLU and Cosine Annealing.
    5. Windows compatibility for make targets (provide direct python commands).
  implication: Documentation needs to be updated with these technical details and the correct sequence of scripts.

- timestamp: 2024-04-18T22:35:00Z
  checked: scripts/ folder
  found: The correct sequence of data preparation and training is:
    1. scripts/setup_dataset.py
    2. scripts/ingest_nutrition5k.py
    3. scripts/setup_foodsam.py
    4. scripts/prepare_data.py --mvp-only
    5. scripts/preprocess_full.py --ids-file data/splits/mvp_subset_ids.txt
    6. scripts/generate_volume_features.py
    7. src/train.py --config configs/experiment/ensemble_mvp.yaml
    8. scripts/verify_results.py
  implication: README.md and strategy_final_2026-04-16.md should reflect this exact workflow.

## Resolution

root_cause: Documentation was outdated and did not reflect the latest script sequence, recent bug fixes (SAM setup, CUDA, metadata column mapping, normalization), or Windows-specific execution paths.
fix: Updated README.md, misc/strategy_final_2026-04-16.md, and docs/PIPELINE_GUIDE.md to reflect the current codebase state, correct data preparation workflow, and recent technical improvements (SCALAR_SCALES, LeakyReLU, etc.).
verification: All updated documents have been cross-checked with scripts/ and .planning/debug/ reports for consistency.
files_changed: ["README.md", "misc/strategy_final_2026-04-16.md", "docs/PIPELINE_GUIDE.md"]