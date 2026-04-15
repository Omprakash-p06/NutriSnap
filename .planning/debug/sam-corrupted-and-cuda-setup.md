---
status: investigating
trigger: "SAM checkpoint corrupted and CUDA not available despite having an NVIDIA GPU."
symptoms:
  expected: "SAM (vit_h) should load successfully and use CUDA for segmentation."
  actual: "Loading fails with PytorchStreamReader error (corrupted zip) and falls back to CPU."
  error_messages: "PytorchStreamReader failed reading zip archive: failed finding central directory"
  timeline: "Fresh setup of the preprocessing pipeline."
  reproduction: "python scripts/run_preprocessing.py --config configs/data/data_config.yaml"
created: 2026-04-15
updated: 2026-04-15
---

# SAM Corrupted and CUDA Setup

## Current Focus
hypothesis: "The SAM weight file is corrupted and the current environment has the CPU-only version of PyTorch installed."
next_action: "Locate and delete the corrupted checkpoint, then reinstall PyTorch with CUDA support."

## Evidence
- timestamp: 2026-04-15T21:40:44Z
  observation: "Logs show 'CUDA not available' and zip archive error during SAM loading."
- timestamp: 2026-04-15T21:45:30Z
  observation: "Checked environment: torch 2.9.1+cpu. Checkpoint file was 1.7GB (corrupted)."

## Next Action
- Fix: Redownload SAM checkpoint and reinstall torch with CUDA.
- Clean: data/interim/ and data/splits/ have been wiped.

## Resolution
root_cause: null
fix: null
verification: null
files_changed: []
