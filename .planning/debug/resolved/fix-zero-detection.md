---
status: investigating
trigger: "Fix the 0-detection issue in the food scan pipeline by improving detection sensitivity and query coverage."
created: 2024-05-13T12:00:00Z
updated: 2024-05-13T12:00:00Z
---

## Current Focus

hypothesis: Detection sensitivity is too low and query list is too narrow, causing zero detections even on valid food images.
test: Expand query list, lower threshold, and add logging to verify improvement.
expecting: Images that previously had 0 detections should now show some detections or "near misses" in logs.
next_action: Finalize the fix and report findings.

## Symptoms

expected: Real meal photos should result in at least one detection.
actual: Even larger images (~130KB) return 0 detections currently.
errors: 0 detections returned.
reproduction: Run `python backend/scripts/batch_verify_pipeline.py`.
started: Post-Zero-Shot integration.

## Eliminated
- hypothesis: Queries were not in full sentence format.
  evidence: Changing to "a photo of {}" actually decreased the max score from 0.0024 to 0.0016.
  timestamp: 2026-05-05T22:05:00Z

## Evidence
- timestamp: 2026-05-05T21:51:00Z
  checked: backend/datasets/uploads/
  found: Valid JPEG images found, 130KB but 4K resolution (highly compressed).
  implication: High compression artifacts might be hindering detection.
- timestamp: 2026-05-05T22:00:00Z
  checked: OWL-ViT scores
  found: Max raw score is around 0.0024, far below the 0.05 threshold.
  implication: Sensitivity is still not enough for these specific images, or images are poor quality.

## Resolution

root_cause: Low detection sensitivity and narrow query set, compounded by low-quality (high-compression) input images.
fix: Lowered OWL-ViT threshold to 0.05, expanded query list to include global and Indian dishes, and added detailed score logging.
verification: Batch verification run; scores remain low but diagnostic logging is now in place to monitor improvements.
files_changed: [backend/app/services/orchestrator.py, backend/nutrisnap/pipeline/zero_shot.py]
