# Codebase Concerns

**Analysis Date:** 2026-04-11

## Tech Debt

**Worktree vs committed architecture drift:**
- Files: current worktree plus committed paths under `backend/`, `frontend/`, `ai_engine/`, `ml/`, and `scripts/`
- Issue: The worktree deletes most of the committed application, while `misc/ARCHITECTURE.md` and `misc/revised_implementationplan.md` describe a new direction
- Why: The branch appears to be transitioning from a full demo app toward a retraining/rebuild effort
- Impact: Planning against the live filesystem alone would be misleading; restoring or replacing behavior needs an explicit decision
- Fix approach: Decide whether the committed app is being retired or reworked, then align code, docs, and planning artifacts around one source of truth

**Prototype-level business logic embedded in routes:**
- Files: `backend/routes/food.py`, `backend/routes/meals.py`, `backend/routes/dashboard.py`
- Issue: Routes do validation, orchestration, persistence, and response shaping directly
- Why: Fast MVP implementation
- Impact: Harder to unit test and risky to refactor because responsibilities are not cleanly separated
- Fix approach: Extract service-layer operations for meal persistence, dashboard aggregation, and food-analysis execution

## Known Bugs

**Database seed script does not match ORM models:**
- Files: `scripts/setup_db.py`, `backend/models/user.py`
- Symptoms: Seeding would fail because the script references fields such as `email`, `height`, `weight`, and `daily_calorie_target` that do not exist on the committed `User` model
- Trigger: Running `python scripts/setup_db.py --seed`
- Workaround: Create tables only; do not use the seed path without fixing model/script alignment
- Root cause: Schema drift between a newer script and older ORM models

**Frontend Docker service is not buildable from `HEAD`:**
- Files: `docker-compose.yml`, `frontend/`
- Symptoms: `docker-compose` expects `frontend/Dockerfile`, but that file is not present in the committed tree
- Trigger: Attempting to build the frontend service from compose
- Workaround: Run the frontend with Vite locally instead of compose
- Root cause: Incomplete containerization for the frontend half of the stack

**Mock detection class IDs are inconsistent with declared class ordering:**
- Files: `ai_engine/agents/detection_agent.py`
- Symptoms: `_mock_detection()` returns `"rice"` with `class_id: 0` and `"dal"` with `class_id: 1`, but `FOOD_CLASSES` is ordered `["dal", "paneer", "rice", "roti"]`
- Trigger: Running the app without a YOLO model present
- Workaround: Treat mock detections as demo-only and do not trust `class_id`
- Root cause: Hard-coded mock payload drifted from the canonical class list

## Security Considerations

**Client-side token handling without server-side auth:**
- Files: `frontend/src/api/client.ts`, `backend/routes/`
- Risk: The frontend implies authenticated requests, but the backend has no authorization layer, making security assumptions easy to get wrong
- Current mitigation: None beyond local/demo usage patterns
- Recommendations: Either remove token handling until auth exists or implement real auth and protect routes explicitly

**Upload validation is minimal:**
- Files: `backend/routes/food.py`
- Risk: Validation checks MIME type only; there is no file-size enforcement, content inspection, or rate limiting
- Current mitigation: Allowed content types are restricted to JPEG/PNG strings and temp files are cleaned up
- Recommendations: Add size limits, image decoding validation, and abuse protection if the endpoint becomes public

## Performance Bottlenecks

**Single-worker analysis executor serializes requests:**
- Files: `backend/routes/food.py`
- Problem: `ThreadPoolExecutor(max_workers=1)` means only one analysis job can run at a time per process
- Measurement: Static code observation; exact latency is not instrumented
- Cause: Conservative offloading of CPU-bound model work
- Improvement path: Move inference to a job queue/process pool or increase worker strategy after measuring model memory needs

**CPU-first model inference can be slow and memory-heavy:**
- Files: `ai_engine/agents/detection_agent.py`, `ai_engine/agents/portion_agent.py`, `ai_engine/models/depth_model.py`, `README.md`
- Problem: YOLO, XGBoost, and depth estimation all run locally, and depth estimation may download/load transformer weights at runtime
- Measurement: No committed benchmarks were found
- Cause: Convenience-first local setup with no batching/caching layer
- Improvement path: Add caching/warmup, optional GPU paths, and explicit performance measurements before production use

## Fragile Areas

**Model path naming is inconsistent:**
- Files: `ai_engine/config/model_config.py`, `ai_engine/agents/detection_agent.py`, `README.md`
- Why fragile: Config defaults refer to `food_detection.pt`, while the detection agent defaults to `yolov8_food.pt`
- Common failures: Confusion over which file should exist in `ml/weights/`
- Safe modification: Standardize the filename contract in one place and update training/export scripts to match
- Test coverage: None

**Current branch state makes file-based assumptions risky:**
- Files: entire repo, especially deleted tracked directories plus `misc/`
- Why fragile: Tools or contributors may assume `backend/` and `frontend/` are present because they exist in `HEAD`, while the local worktree has removed them
- Common failures: Broken commands, incorrect planning, or accidental recreation of code that the user intentionally deleted
- Safe modification: Check `git status` and planning docs before making structural changes
- Test coverage: None

## Scaling Limits

**SQLite and local filesystem deployment model:**
- Files: `backend/config.py`, `backend/database.py`, `backend/routes/food.py`
- Current capacity: Small local/demo usage
- Limit: Single-node storage and local temp file handling do not scale cleanly to multi-instance deployment
- Symptoms at limit: file contention, inconsistent local state, and database write bottlenecks
- Scaling path: Move to a managed database/object storage pair and introduce background job processing

## Dependencies at Risk

**Runtime dependency on remote model availability:**
- Files: `ai_engine/models/depth_model.py`
- Risk: First-run success depends on being able to download or resolve the Depth Anything model
- Impact: Offline or locked-down environments may lose depth support silently
- Migration plan: Vendor or pre-download required model artifacts and check availability at startup

## Missing Critical Features

**No real authentication or user isolation:**
- Files: `backend/routes/meals.py`, `backend/routes/dashboard.py`, `frontend/src/api/client.ts`
- Problem: The app behaves like a single-user demo with `user_id=1` defaults
- Current workaround: Demo user assumptions in route logic
- Blocks: Secure multi-user deployment, per-user privacy, and trustworthy account-based features
- Implementation complexity: Medium

**No automated regression suite:**
- Files: repo-wide; see `requirements.txt` and lack of test files
- Problem: There is no safety net for route changes, schema changes, or ML fallback behavior
- Current workaround: Manual local smoke testing
- Blocks: Safe refactoring, high-confidence cleanup of the current restructure
- Implementation complexity: Medium

## Test Coverage Gaps

**Inference pipeline and route contracts are effectively untested:**
- Files: `backend/routes/food.py`, `ai_engine/coordinator.py`, `ai_engine/agents/*.py`
- What's not tested: upload handling, model fallback behavior, grouped detection logic, and response schema stability
- Risk: Changes could break the core value path without being noticed until manual testing
- Priority: High
- Difficulty to test: Medium; requires model stubbing or fixture images

**Persistence and dashboard aggregation are untested:**
- Files: `backend/routes/meals.py`, `backend/routes/dashboard.py`
- What's not tested: CRUD behavior, cascade delete expectations, and daily/weekly aggregate correctness
- Risk: Silent data corruption or broken dashboard summaries
- Priority: High
- Difficulty to test: Low to medium with a SQLite test database

---
*Concerns audit: 2026-04-11*
*Update as issues are fixed, clarified, or intentionally accepted*
