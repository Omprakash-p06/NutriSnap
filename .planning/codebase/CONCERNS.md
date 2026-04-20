# Codebase Concerns

**Analysis Date:** 2026-04-18

## Tech Debt

**Modular Transition Completion:**
- **Issue:** While the core package has been restructured, some legacy scripts or documentation might still refer to the old `backend/` or `ai_engine/` paths.
- **Impact:** Potential confusion for new contributors.
- **Fix approach:** Finalize the cleanup of all non-functional root-level directories and ensure all documentation (including this file) is updated.

**Configuration Complexity:**
- **Issue:** The hierarchical configuration in `configs/` is flexible but can become difficult to manage without clear documentation on each parameter's effect.
- **Impact:** Increased risk of misconfiguration during training or deployment.
- **Fix approach:** Add a `CONFIG_GUIDE.md` to `docs/` explaining the configuration schema.

## Known Bugs

**FoodSAM Setup Fragility:**
- **Issue:** The `setup_foodsam.py` script relies on specific environment conditions and manual checkpoint downloads.
- **Symptoms:** Segmentation stage might fail if weights are not correctly placed.
- **Fix approach:** Automate checkpoint downloads using `kagglehub` or similar if possible.

**Asynchronous Job Timeouts:**
- **Issue:** Very large images or high-latency LLM calls (Gemini) might cause job processing to exceed expected timeframes.
- **Impact:** Possible worker stalls or client-side polling timeouts.
- **Fix approach:** Implement per-stage timeouts in the `InferencePipeline`.

## Security Considerations

**Unprotected API Endpoints:**
- **Issue:** The FastAPI application currently has no authentication or rate-limiting layers.
- **Risk:** Public exposure could lead to resource exhaustion or abuse.
- **Mitigation:** Intended for local/private usage, but requires JWT or API Key auth before public deployment.

**Unvalidated File Uploads:**
- **Issue:** Minimal validation of uploaded image contents beyond extension checks.
- **Risk:** Malicious file uploads.
- **Mitigation:** Add image size limits and verify image integrity using Pillow before processing.

## Performance Bottlenecks

**Serial Background Worker:**
- **Issue:** `JobWorker` currently processes jobs one by one.
- **Impact:** Scaling to multiple concurrent users will result in significant wait times.
- **Improvement path:** Transition to a multi-process worker pool or a dedicated task queue like Celery/Redis.

**In-Memory/Local Result Store:**
- **Issue:** `ResultStore` uses a local SQLite database.
- **Impact:** Cannot scale horizontally across multiple API instances.
- **Improvement path:** Support for PostgreSQL or a centralized database.

## Fragile Areas

**External API Dependencies:**
- **Issue:** High reliance on Gemini and USDA APIs for fallbacks and verification.
- **Risk:** Service outages or API key exhaustion can break the 'reliability' promise of the pipeline.
- **Mitigation:** Improved local fallbacks and aggressive caching of USDA data.

**Model Checkpoint Compatibility:**
- **Issue:** Changes to model architecture in `src/nutrisnap/models/` can silently break compatibility with existing checkpoints in `models/checkpoints/`.
- **Mitigation:** Implement model versioning and validation checks during loading.

## Missing Critical Features

**User Authentication:**
- **Status:** Not implemented.
- **Priority:** High for any multi-user deployment.

**Frontend Interface:**
- **Status:** The original React frontend was removed during the restructure.
- **Priority:** Required for a complete end-to-end user experience.

**Comprehensive Monitoring:**
- **Status:** No real-time dashboard for pipeline health or model performance metrics.
- **Priority:** Medium for operational stability.

## Test Coverage Gaps

**Edge Case Image Handling:**
- **Gap:** Limited tests for corrupted images, extremely high resolutions, or non-food images.
- **Priority:** Medium.

**Load Testing:**
- **Gap:** No current benchmarks for how the system behaves under concurrent job requests.
- **Priority:** High before any production-like deployment.

---
*Concerns audit: 2026-04-18*
