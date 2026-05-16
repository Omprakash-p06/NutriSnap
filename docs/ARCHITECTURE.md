# NutriSnap Final Architecture (2026-05-06)

## 1) Canonical Scope and Source of Truth

This document is the canonical architecture reference for the active NutriSnap monorepo.

Primary architecture artifacts:
- `docs/ARCHITECTURE.md` (this file): authoritative narrative and directory-level architecture.
- `docs/architecture.svg`: authoritative visual architecture for the active inference/application system.

Historical/secondary artifacts:
- `backend/misc/revised_architecture.svg`: legacy preprocessing/training-focused flow (reference only).
- `backend/misc/revised architecture.mermaid`: corresponding source for the legacy flow.
- `.planning/codebase/ARCHITECTURE.md`: planning scaffold, not the current production truth.

## 2) Monorepo Topology

At the repository root:
- `backend/`: Python backend, ML orchestration, API, tests, configs, scripts, datasets, and reports.
- `frontend/`: React 19 + Vite + PWA client app.
- `docs/`: top-level architecture visual and final architecture narrative.
- `.planning/`: debug/planning state, including active and resolved debug sessions.
- Root helper files: `docker-compose.yml`, `start.py`, `test_api.py`, `test_inference.py`, `README.md`.

Important note:
- The importable `nutrisnap` Python package is under `backend/nutrisnap/` (not at repository root).

### 2.1 Minute Root Directory Map

- `.github/`: CI automation and workflow definitions.
- `.planning/`: milestone state, execution plans, debug files, and verification artifacts.
- `.planning_backup/`: prior planning snapshots retained for rollback/comparison.
- `backend/`: all Python runtime, models, data, scripts, and infrastructure for API + inference.
- `frontend/`: React/Vite/PWA product surface and static build artifacts.
- `docs/`: canonical architecture narrative and SVG.
- `docker-compose.yml`: local multi-service orchestration entry.
- `start.py`: root bootstrap helper for development workflows.
- `test_api.py`, `test_inference.py`: root-level smoke/integration helpers.
- `yolov8n.pt`: fallback/reference detector weight available at root.

## 3) Backend Architecture

### 3.1 Backend root layout (`backend/`)

Key directories:
- `backend/app/`: FastAPI application entrypoint, routers, services, middleware, schemas, utilities.
- `backend/nutrisnap/`: model/pipeline package for training, inference, verification, and API worker flow.
- `backend/configs/`: API/model/pipeline and experiment configuration.
- `backend/data/`, `backend/datasets/`: food database artifacts, uploads, and data assets.
- `backend/models/`: serialized trained artifacts/checkpoints.
- `backend/scripts/`: diagnostics, verification, and data prep scripts.
- `backend/tests/`: backend test suite.
- `backend/misc/`: historical plans, alternate diagrams, and architecture drafts.

Operational files:
- `backend/app/main.py`: FastAPI app composition, startup/shutdown lifecycle, orchestrator initialization.
- `backend/requirements.txt`, `backend/pyproject.toml`: dependency and tooling definitions.

Backend operational/support directories observed in current tree:
- `backend/configs/`: centralized YAML config groups for API/data/model/pipeline/experiments.
- `backend/data/`: curated data sources such as food databases and ingredient reference CSV.
- `backend/datasets/`: mutable runtime/training assets (`external/`, `uploads/`).
- `backend/reports/`: audit and evaluation outputs, including batch verification results.
- `backend/scratch/`: one-off diagnostics and experiment scripts (checkpoint checks, mask/depth verification, VRAM probes).
- `backend/scripts/`: reusable operational scripts (prepare data, verify pipeline, generate volume features, repair GPU).
- `backend/tests/`: unit/integration tests for API, pipeline, and service surfaces.
- `backend/notebooks/`: exploratory notebooks for model and data analysis.
- `backend/models/`: serialized model artifacts (regressors, calibrators, checkpoints).
- `backend/logs/`: runtime logging and troubleshooting traces.
- `backend/misc/`: historical architecture files and implementation strategy documents.
- `backend/venv/`: local Python environment folder (workspace-local execution dependency).

### 3.2 FastAPI app composition (`backend/app/`)

Core files:
- `backend/app/main.py`: application lifecycle, router registration, CORS, rate limiting, orchestrator boot.
- `backend/app/database.py`: database connectivity lifecycle.
- `backend/app/middleware.py`: request-level middleware.
- `backend/app/schemas.py`: request/response schema definitions.
- `backend/app/exceptions.py`: centralized exception handling.

Routers (`backend/app/routers/`):
- `auth.py`, `users.py`: account/auth domains.
- `food.py`, `water.py`, `logs.py`: nutrition/water logging and food endpoints.
- `prediction.py`: photo-based nutrition prediction endpoints.
- `planning.py`, `insights.py`: planning and analysis routes.
- `chat.py`: Gemini-assisted websocket chat flow.
- `health.py`: liveness/health and monitoring endpoints.
- `social.py`: social/community features.

Services (`backend/app/services/`):
- `orchestrator.py`: sequential multi-stage CV + nutrition inference pipeline orchestration.
- `mapping.py`: ingredient and mapping support.
- `task_manager.py`: async job/task state and cleanup.

Utilities (`backend/app/utils/`):
- `nutrition.py`, `mapping.py`, `tasks.py`: helper logic used by routes/services.

### 3.3 `backend/nutrisnap/` package role

The `backend/nutrisnap/` package provides deeper ML stack capabilities:
- `api/`: worker-level orchestration and API-adjacent model workflow.
- `pipeline/`, `inference/`: model inference pipeline components.
- `training/`, `train.py`, `evaluate.py`, `evaluate_efficientnet.py`: training/evaluation flow.
- `verification/`: validator and LLM fallback logic.
- `models/`, `data/`, `utils/`: reusable package internals.
- `ensemble.py`, `predict.py`: ensemble and prediction entry scripts.

## 4) Frontend Architecture (`frontend/`)

Tech/runtime:
- React 19 application with Vite 8 build tooling.
- PWA enabled via `vite-plugin-pwa`.
- Local persistence via Dexie.
- Charts/UX components via Recharts and Framer Motion.

Structure:
- `frontend/src/pages/`: page-level composition (`Home.jsx` includes scan-result UX).
- `frontend/src/components/`: reusable UI modules, including `scanning/MultiFoodDisplay.jsx`.
- `frontend/src/services/`: API integration layer.
- `frontend/src/context/`, `frontend/src/hooks/`: shared state and behavior.

Additional frontend directories and artifacts:
- `frontend/public/`: static assets served directly.
- `frontend/server/`: frontend-side server utilities and local integrations.
- `frontend/elements/`: component primitives and reusable visual building blocks.
- `frontend/dev-dist/` and `frontend/dist/`: generated build artifacts (including service worker output).
- `frontend/misc/`: supporting docs and implementation notes.
- `frontend/init.json`, `frontend/GEMINI.md`: runtime bootstrap and AI-assistant integration notes.

Backend integration:
- `frontend/vite.config.js` proxies `/api` and `/ws` to `localhost:5000` in dev.

## 5) Runtime Integration Contracts

### 5.1 Port and proxy alignment

- Backend dev runtime is bound to port 5000 (`backend/app/main.py`).
- Frontend Vite dev proxy targets `http://localhost:5000` and `ws://localhost:5000`.

### 5.2 Inference pipeline (active system)

As represented by `docs/architecture.svg` and backend orchestration:
1. Image upload from frontend/user.
2. Detection stage (OWL-ViT primary, YOLOv8 support/filtering path).
3. Segmentation stage (SAM-family path for instance masks).
4. Depth estimation stage (GLPN path).
5. Fusion/merger stage for volume/mass/nutrition derivation.
6. Optional LLM-assisted refinement/validation (Gemini path where configured).
7. Structured pipeline result returned to API/frontend consumers.

### 5.3 Data and persistence

- Backend keeps domain data assets under `backend/data/`.
- Uploads and processing artifacts are managed in `backend/datasets/` and pipeline outputs.
- SQLite and/or configured stores are used by backend runtime depending on component path.

## 6) Documentation Drift Analysis and Hardships

### 6.1 Root cause of drift

Documentation evolved in multiple places (`backend/misc/`, `docs/`, `.planning/`) without a single enforced canonical artifact pair for final architecture text + visual.

### 6.2 Observed drift patterns

- Multiple architecture markdown files with conflicting depth and recency.
- Presence of historical diagrams that model training/data prep instead of current product inference architecture.
- Visual label staleness in `docs/architecture.svg` (frontend stack wording drifted from actual dependencies).
- Planning documents mixed with production docs and treated as if equally authoritative.

### 6.3 Debug history (resolved sessions)

Resolved sessions in `.planning/debug/resolved/`:
- `backend-port-access-forbidden.md`
  - Problem: backend launch failed on port 8000 (`WinError 10013`).
  - Resolution direction: align backend to 5000 to match frontend proxy and avoid host conflict.
- `missing-dependency-email-validator.md`
  - Problem: startup `ImportError` for missing `email-validator`.
  - Resolution direction: add dependency to backend requirements.
- `fix-zero-detection.md`
  - Problem: 0 detections in scan flow due to low sensitivity and narrow query coverage.
  - Resolution direction: threshold tuning + broader food query list + diagnostic logging.
- `ci-structure-mismatch-and-lint.md`
  - Problem: CI pointed to old root-level paths after backend/frontend split and lint issues in backend.
  - Resolution direction: CI path updates and lint remediation.

### 6.4 Active investigation threads (not yet resolved)

Active debug session files currently present in `.planning/debug/`:
- `advanced-preprocessing-tiling.md`
- `ci-fix-dependencies-paths-lint.md`
- `comprehensive-pipeline-verification.md`
- `comprehensive-security-audit.md`
- `final-documentation-and-architecture-update.md`
- `food-detection-vulnerability.md`
- `frontend-backend-integration-audit.md`
- `frontend-routing-onboarding.md`
- `hardcoded-biryani-scan-result.md`
- `mapping-confirmation.md`
- `model-source-verification.md`
- `onboarding-expansion-pipeline-verify.md`
- `pipeline-refinement-optimization.md`
- `remove-auth-and-updates.md`
- `knowledge-base.md` (cumulative learned fixes and patterns)
- `git-commit-standards.md` (workflow reliability guardrail)

These indicate ongoing architecture pressure areas:
- Platform hardening and security posture.
- Inference reliability and data quality edge cases.
- Frontend-backend contract stability.
- Operational standards and workflow consistency.

### 6.5 Hardships and recurring failure modes observed

- Port contract drift: backend host/port mismatches created frontend API and websocket failures until fixed to a shared 5000 contract.
- Dependency drift: environment-level missing packages (example: `email-validator`) blocked app startup.
- CI drift after repo evolution: path assumptions in workflows became invalid after backend/frontend separation.
- Detection sensitivity failures: overly strict thresholds and narrow query sets produced empty detections for real food images.
- Documentation divergence: multiple architecture artifacts evolved in parallel with no enforced canonical pair.
- Reliability pressure from optional AI dependencies: Gemini-based validation/refinement paths require graceful degradation when keys or quotas are unavailable.

## 7) Final Artifact Governance

To prevent recurrent drift:
- Keep only one active architecture visual at top-level docs: `docs/architecture.svg`.
- Keep one canonical narrative: `docs/ARCHITECTURE.md`.
- Treat `backend/misc/*architecture*` artifacts as historical references unless explicitly promoted.
- On every major pipeline or directory change:
  1. Update `docs/architecture.svg` in place (preserve visual language unless redesign is intentional).
  2. Update sections 2-6 in this file.
  3. Record key changes in `.planning/debug` or milestone documentation.

## 8) 2026-05-06 Finalization Changes

Applied in this finalization:
- Kept `docs/architecture.svg` as the canonical visual architecture artifact.
- Updated frontend stack label in `docs/architecture.svg` from stale Tailwind wording to current stack wording.
- Added this `docs/ARCHITECTURE.md` with consolidated, directory-level architecture and debug-hardship history.

Status after finalization:
- Architecture visual and architecture narrative are now aligned to current repository structure and runtime contracts.
