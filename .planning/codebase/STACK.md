# Technology Stack

**Analysis Date:** 2026-04-11

**Mapping basis:** The runtime application described below comes from `HEAD`, because the current worktree has most tracked app directories deleted (`git diff --stat` shows large removals across `backend/`, `frontend/`, `ai_engine/`, `ml/`, and `scripts/`). Treat this as the latest committed stack plus a note that the branch is currently in a retraining/restructure state.

## Languages

**Primary:**
- Python 3.10+ - Backend API, AI inference, model training, and utility scripts in `backend/`, `ai_engine/`, `ml/`, and `scripts/`
- TypeScript 5.9 - Frontend application code in `frontend/src/`

**Secondary:**
- JavaScript (ES modules) - Frontend tooling config in `frontend/eslint.config.js`, `frontend/postcss.config.js`, and `frontend/tailwind.config.js`
- YAML and JSON - Model/data configuration in `configs/*.yaml` and nutrition/class data in `data/**/*.json`
- Markdown - Repo documentation in `README.md`, `misc/ARCHITECTURE.md`, and `misc/revised_implementationplan.md`

## Runtime

**Environment:**
- Python application server via `uvicorn` running `backend.main:app`
- Browser runtime for the React single-page app mounted from `frontend/src/main.tsx`
- Local CPU-first ML inference; `README.md` explicitly says models are configured for CPU by default

**Package Manager:**
- pip - Python dependencies are pinned loosely in `requirements.txt`
- npm - Frontend dependencies managed through `frontend/package.json`
- Lockfile: `frontend/package-lock.json` is present in `HEAD`

## Frameworks

**Core:**
- FastAPI 0.110+ - HTTP API and schema-driven request handling in `backend/main.py`
- SQLAlchemy 2.x - ORM and SQLite session management in `backend/database.py`
- Pydantic 2.x / pydantic-settings - API schemas and environment config in `backend/config.py`
- React 19.2 - Frontend UI in `frontend/src/`
- React Router DOM 7.13 - Client routing in `frontend/src/App.tsx`

**ML / CV:**
- Ultralytics YOLO 8.x - Food detection in `ai_engine/agents/detection_agent.py` and `ml/train_yolo.py`
- XGBoost 2.x - Portion estimation model in `ai_engine/agents/portion_agent.py` and `ml/train_portion.py`
- Transformers 4.38+ - Depth Anything V2 depth estimation in `ai_engine/models/depth_model.py`
- OpenCV / NumPy / Pillow - Image preprocessing and CV utilities in `backend/services/preprocessing.py`

**Build / Dev:**
- Vite 7.3 - Frontend dev server and bundling
- TypeScript compiler - Frontend build step (`npm run build`)
- ESLint 9.x with `typescript-eslint` and React plugins - Frontend linting via `frontend/eslint.config.js`
- Docker / docker-compose - Local containerized backend and intended full-stack orchestration via `Dockerfile` and `docker-compose.yml`

## Key Dependencies

**Critical:**
- `fastapi` - API routing and request validation
- `sqlalchemy` + `aiosqlite` - Local persistence using SQLite
- `ultralytics` - Detection model loading and inference
- `xgboost` + `joblib` - Portion estimation model training and loading
- `transformers` - Depth estimation model pipeline
- `axios` - Frontend HTTP client in `frontend/src/api/client.ts`
- `recharts` - Nutrition visualizations in dashboard components

**Infrastructure:**
- `python-multipart` - File uploads for `/api/v1/analyze`
- `uvicorn[standard]` - ASGI server
- `tailwindcss` + `postcss` + `autoprefixer` - Frontend styling pipeline

## Configuration

**Environment:**
- Root `.env` is read by `backend/config.py`
- Frontend can use `frontend/.env` for `VITE_API_URL`
- Key backend vars: `DATABASE_URL`, `MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `IMAGE_SIZE`, `ENV`

**Build:**
- `requirements.txt` - Python dependency manifest
- `frontend/package.json` - Frontend scripts and dependencies
- `frontend/vite.config.ts`, `frontend/tsconfig*.json`, `frontend/eslint.config.js`
- `configs/yolo_train.yaml` and `configs/portion_model.yaml` for training configuration

## Platform Requirements

**Development:**
- Windows/Linux/macOS can run the repo, but OpenCV system libraries are required in containers
- Node.js 18+ and Python 3.10+ are called out in `README.md`
- Local model weights are expected under `ml/weights/`

**Production / Deployment Shape:**
- Backend is designed to run in Docker from `Dockerfile`
- Frontend is a Vite SPA; `docker-compose.yml` expects a separate frontend image, although `HEAD` does not include `frontend/Dockerfile`
- Current branch state suggests a likely transition toward a retraining-focused architecture described in `misc/revised_implementationplan.md`

---
*Stack analysis: 2026-04-11*
*Update after major dependency changes or after the current restructure lands*
