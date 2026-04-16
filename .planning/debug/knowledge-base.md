# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## cleanup-training-artifacts — Clear training data to start fresh
- **Date:** 2024-05-15
- **Error patterns:** cleanup, training artifacts, checkpoints, clear, fresh start
- **Root cause:** Previous training run left behind checkpoints and temporary files.
- **Fix:** Manually deleted `models/checkpoints/` experiment subdirectories and temporary split files `data/splits/_tmp_*.txt`.
- **Files changed:** None
---
