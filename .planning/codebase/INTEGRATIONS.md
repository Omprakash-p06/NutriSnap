# External Integrations

**Analysis Date:** 2026-04-11

**Mapping basis:** This audit reflects `HEAD` plus the current worktree state. The committed application is mostly local-first and self-contained; `misc/revised_implementationplan.md` describes additional future integrations that are not yet implemented.

## APIs & External Services

**Model downloads / external ML assets:**
- Hugging Face model hub - Depth estimation can be pulled dynamically by `transformers.pipeline()` in `ai_engine/models/depth_model.py`
  - Integration method: Python `transformers` pipeline download at runtime
  - Auth: None shown in code
  - Operational note: First run may require network access and local cache space

**Utility download tooling:**
- `gdown` is listed in `requirements.txt`
  - Usage: likely intended for model/dataset retrieval workflows
  - Auth: None documented
  - Status: no active integration point was found in committed runtime code

**Planned but not implemented:**
- `misc/revised_implementationplan.md` proposes optional Gemini/Grok validation fallback
  - Status: planning-only; no API client or route implementation exists in `HEAD`

## Data Storage

**Databases:**
- SQLite - Primary application storage
  - Connection: `DATABASE_URL` / `settings.database_url`
  - Client: SQLAlchemy ORM in `backend/database.py`
  - Schema source: `backend/models/user.py`, `backend/models/meal.py`, `backend/models/food_item.py`

**File storage:**
- Local filesystem - Uploaded images are written temporarily to `temp_uploads/` in `backend/routes/food.py`
  - Cleanup: file is removed in the route `finally` block
- Local filesystem - Model weights expected under `ml/weights/`
- Local filesystem - Nutrition lookup JSON stored in `data/nutrition_db/nutrition.json` and `data/nutrition_db/food_mappings.json`

**Caching:**
- None found
- No Redis, in-memory cache service, or queue backend is configured in `HEAD`

## Authentication & Identity

**Auth provider:**
- None implemented on the backend
  - Backend routes use default/demo user behavior (`user_id=1`) in `backend/routes/meals.py` and `backend/routes/dashboard.py`
  - No JWT middleware, login routes, password flows, or auth provider config were found

**Frontend token handling:**
- `frontend/src/api/client.ts` reads `token` from `localStorage`
  - Implementation: Axios request interceptor attaches `Authorization: Bearer ...`
  - Session management: client-only placeholder; backend does not appear to honor it

## Monitoring & Observability

**Health checks:**
- Internal health endpoint at `GET /health` in `backend/routes/health.py`
- Docker healthcheck in `Dockerfile` calls the health endpoint

**Logs / error tracking:**
- No Sentry, Datadog, or centralized logging integration found
- Runtime logging is mostly `print`, `traceback.print_exc()`, and `console.error`

**Analytics:**
- None found in committed frontend or backend code

## CI/CD & Deployment

**Hosting shape:**
- Backend container image defined by root `Dockerfile`
- Local composition intended via `docker-compose.yml`

**CI pipeline:**
- No `.github/workflows/` directory exists in `HEAD`
- No CI config, deployment manifests, or release automation was found

## Environment Configuration

**Development:**
- Root `.env` for backend settings via `backend/config.py`
- `frontend/.env` may set `VITE_API_URL`
- Critical vars surfaced by code or docs: `DATABASE_URL`, `MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `IMAGE_SIZE`, `ENV`, `VITE_API_URL`

**Production:**
- Docker sets `ENV=production` and `PYTHONPATH=/app`
- Secrets management is not documented beyond env vars
- No staging/production environment split is defined in code

## Webhooks & Callbacks

**Incoming:**
- None found

**Outgoing:**
- None found

## Integration Gaps To Remember

- `frontend/src/api/client.ts` assumes bearer-token auth, but `backend/` has no auth implementation
- `docker-compose.yml` references a frontend Docker build that is not present in `HEAD`
- Future AI fallback/API validation exists only in `misc/revised_implementationplan.md`, not in runnable code

---
*Integration audit: 2026-04-11*
*Update when adding remote services, auth, storage providers, or CI/CD*
