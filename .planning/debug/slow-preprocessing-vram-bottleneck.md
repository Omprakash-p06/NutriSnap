---
status: investigating
trigger: "Investigate and fix extremely slow preprocessing (19s/frame) on RTX 3050 (4GB VRAM)."
created: 2024-05-15T12:00:00Z
updated: 2024-05-15T12:00:00Z
---

## Current Focus

hypothesis: VRAM is nearly exhausted by system/other apps (~3.5GB/4GB used), leaving <600MB for NutriSnap. Co-existence of SAM 2 and GLPN models on GPU, along with high SAM 2 point density, causes extreme swapping/slowness.
test: Implement sequential model loading (unload between depth and segmentation) and reduce SAM 2 point density. Use FP16 if possible.
expecting: Significant speedup by staying within the remaining VRAM and reducing SAM 2 compute.
next_action: implement model unloading and optimization

## Symptoms

expected: Sub-second or low-second processing per frame on GPU.
actual: 18-20 seconds per frame.
errors: "You seem to be using the pipelines sequentially on GPU..." warning.
reproduction: python scripts/preprocess_full.py --mvp-only --sampling-rate 50
started: Observed during expanded 20-dish MVP preprocessing.

## Eliminated


## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2024-05-15T12:05:00Z
  checked: scripts/preprocess_full.py, src/nutrisnap/pipeline/segmenter.py, src/nutrisnap/pipeline/depth.py
  found: SAM 2 and GLPN models are both loaded and kept on GPU during the 3-stage preprocessing. SAM 2 mask generation is performed image-by-image within the batch loop.
  implication: Combined VRAM usage might be exceeding 4GB, leading to slow processing due to VRAM swapping.

- timestamp: 2024-05-15T12:06:00Z
  checked: src/nutrisnap/pipeline/segmenter.py (FoodSegmenterSAM2.segment_batch)
  found: The transformers pipeline for mask-generation is used. points_per_crop is set to 16. It doesn't use the model's native batching capabilities effectively because of a mentioned bug in the transformers pipeline.
  implication: Inference is sequential per image in the batch, and SAM 2 Automatic Mask Generation is notoriously heavy on memory/compute if not tuned.

- timestamp: 2024-05-15T12:15:00Z
  checked: nvidia-smi
  found: GPU (RTX 3050 4GB) is already using 3519MiB / 4096MiB due to numerous background processes (Discord, Edge, Spotify, etc.). Only ~577MiB available.
  implication: NutriSnap is fighting for very limited VRAM. Keeping both models on GPU is impossible without severe swapping. SAM 2 Automatic Mask Generation is likely hitting the system RAM.

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
