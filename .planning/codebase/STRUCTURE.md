# Codebase Structure

**Analysis Date:** 2025-05-15

## Directory Layout

```
[project-root]/
├── backend/            # Python FastAPI Backend
│   ├── app/            # Web API logic
│   ├── configs/        # Hydra/YAML configurations
│   ├── data/           # Local databases (JSON/CSV)
│   ├── models/         # Local model weights and LLM storage
│   ├── nutrisnap/      # Core ML inference engine
│   ├── scripts/        # Setup and utility scripts
│   └── tests/          # Pytest suite
├── frontend/           # Vite + React Frontend
│   ├── public/         # Static assets
│   └── src/            # React source code
├── .github/            # GitHub Actions CI/CD
├── .planning/          # GSD Project Management
└── docs/               # Technical documentation
```

## Directory Purposes

**backend/app/:**
- Purpose: FastAPI application structure
- Contains: Routers, services, schemas, and database logic
- Key files: `main.py`, `auth.py`, `database.py`

**backend/nutrisnap/:**
- Purpose: Core ML logic and model wrappers
- Contains: Inference pipelines and utility functions
- Key files: `utils/local_llm_backend.py`

**backend/scripts/:**
- Purpose: Automation and maintenance
- Contains: Model downloaders and environment setup scripts
- Key files: `download_models.py`, `setup_local_llm.py`

**frontend/src/:**
- Purpose: User interface source
- Contains: Components, pages, hooks, and assets

## Key File Locations

**Entry Points:**
- `setup.py`: Initial environment setup
- `start.py`: Orchestrator to run frontend, backend, and LLM servers
- `backend/app/main.py`: FastAPI server entry
- `frontend/src/main.jsx`: React entry

**Configuration:**
- `backend/.env.example`: Template for backend environment variables
- `frontend/.env.example`: Template for frontend environment variables
- `backend/configs/main.yaml`: Main configuration for ML pipelines

**Core Logic:**
- `backend/nutrisnap/`: Primary ML inference logic
- `backend/app/services/`: Business logic layer

**Testing:**
- `backend/tests/`: Backend test suite
- `.github/workflows/`: CI/CD automation

## Naming Conventions

**Files:**
- Backend: snake_case (e.g., `model_loader.py`)
- Frontend: PascalCase for components (e.g., `ScanButton.jsx`), camelCase for hooks (e.g., `useAuth.js`)

**Directories:**
- snake_case throughout

## Where to Add New Code

**New Feature:**
- Backend logic: `backend/app/services/`
- Backend endpoint: `backend/app/routers/`
- Frontend page: `frontend/src/pages/`

**New Component/Module:**
- Implementation: `frontend/src/components/`
- ML Model wrapper: `backend/nutrisnap/`

**Utilities:**
- Backend: `backend/app/utils/` or `backend/nutrisnap/utils/`
- Frontend: `frontend/src/utils/`

## Special Directories

**backend/venv/:**
- Purpose: Python virtual environment
- Generated: Yes
- Committed: No

**frontend/node_modules/:**
- Purpose: Node.js dependencies
- Generated: Yes
- Committed: No

**backend/models/llm/:**
- Purpose: GGUF models for local inference
- Generated: Yes (via setup script)
- Committed: No

---

*Structure analysis: 2025-05-15*
