# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## fix-zero-detection — Improved food detection sensitivity and coverage
- **Date:** 2026-05-05
- **Error patterns:** 0 detections, low confidence scores, OWL-ViT sensitivity
- **Root cause:** Low detection sensitivity and narrow query set, compounded by low-quality input images.
- **Fix:** Lowered OWL-ViT threshold to 0.05, expanded query list to include global and Indian dishes, and added detailed score logging.
- **Files changed:** backend/app/services/orchestrator.py, backend/nutrisnap/pipeline/zero_shot.py
---
