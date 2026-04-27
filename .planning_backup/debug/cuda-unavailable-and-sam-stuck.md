---
status: investigating
trigger: "Investigate and fix CUDA unavailability and 'stuck' SAM masking pass. Also, verify implementation of Swin Transformer and EfficientNetV2B0."
created: 2024-05-15T12:00:00Z
updated: 2024-05-15T12:00:00Z
---

## Current Focus

hypothesis: CUDA is not available due to environment configuration or missing drivers/libraries. SAM is stuck because it's running on CPU with 10,072 items which is too many for a "10-dish MVP".
test: Check CUDA availability in python, check environment variables, and verify the input IDs file content.
expecting: `torch.cuda.is_available()` to be False, and `data/splits/mvp_subset_ids.txt` to potentially have more than 10 IDs or SAM is expanding them incorrectly.
next_action: Run diagnostic script for CUDA and check the IDs file.

## Symptoms

expected: Preprocessing (SAM masking) runs quickly using CUDA for the 10-dish MVP subset.
actual: "CUDA not available — falling back to CPU (slow)", and SAM Masking is stuck at "0/10072 [00:00<?, ?it/s]".
errors: "WARNING | nutrisnap.pipeline.segmenter | CUDA not available — falling back to CPU (slow)"
reproduction: python scripts/preprocess_full.py --ids-file data/splits/mvp_subset_ids.txt --output-dir data/processed/features
started: Just started during MVP preprocessing.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
