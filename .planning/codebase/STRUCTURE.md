# Codebase Structure

**Analysis Date:** 2026-04-11

**Mapping basis:** The tree below reflects the committed project layout in `HEAD`. The current worktree keeps only a subset of those files locally and deletes most runtime directories, so use this map as the committed baseline plus a warning that the branch is in flux.

## Directory Layout

```text
NutriSnap/
├── ai_engine/          # Inference coordinator, agents, and model wrappers
│   ├── agents/         # Detection, portion, and nutrition agent classes
│   ├── config/         # Model path / threshold config
│   ├── models/         # Depth, YOLO, segmentation, and portion model wrappers
│   └── tools/          # Image and nutrition helper utilities
├── backend/            # FastAPI app, routes, schemas, ORM models, and services
│   ├── models/         # SQLAlchemy tables
│   ├── routes/         # API routers
│   ├── schemas/        # Pydantic request/response contracts
│   └── services/       # Nutrition, metrics, and preprocessing helpers
├── configs/            # Training-time YAML config files
├── data/               # SQLite DB, nutrition JSON, labels, and raw dataset assets
├── frontend/           # React + Vite SPA
│   ├── public/         # Static assets
│   └── src/            # Pages, components, API wrappers, utilities
├── ml/                 # Training and evaluation scripts
├── misc/               # Architecture / implementation notes for the current redesign
├── scripts/            # Developer maintenance scripts
├── Dockerfile          # Backend container definition
├── docker-compose.yml  # Intended full-stack local orchestration
├── README.md           # Setup and project overview
└── requirements.txt    # Python dependencies
```

## Directory Purposes

**`ai_engine/`:**
- Purpose: Runtime inference pipeline for food analysis
- Contains: coordinator, per-task agents, lazy model loaders, helper tools
- Key files: `ai_engine/coordinator.py`, `ai_engine/agents/detection_agent.py`, `ai_engine/agents/portion_agent.py`
- Subdirectories: `agents/`, `config/`, `models/`, `tools/`

**`backend/`:**
- Purpose: Web API, database setup, serialization, and business endpoints
- Contains: FastAPI app factory, routers, ORM models, schemas, and preprocessing helpers
- Key files: `backend/main.py`, `backend/database.py`, `backend/routes/food.py`, `backend/routes/meals.py`
- Subdirectories: `models/`, `routes/`, `schemas/`, `services/`

**`frontend/`:**
- Purpose: User-facing application for scanning food and viewing meal history
- Contains: Vite config, React pages/components, API wrappers, CSS
- Key files: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/pages/Scan.tsx`, `frontend/package.json`
- Subdirectories: `src/components/`, `src/pages/`, `src/api/`, `public/`

**`ml/`:**
- Purpose: Offline model training, evaluation, and preprocessing
- Contains: Python scripts for YOLO, portion estimation, depth work, and EDA
- Key files: `ml/train_yolo.py`, `ml/train_portion.py`, `ml/evaluate.py`
- Subdirectories: flat script layout in `HEAD`

**`data/`:**
- Purpose: Application data and static model inputs
- Contains: nutrition JSON, class labels, raw dataset directories, SQLite database path
- Key files: `data/nutrition_db/nutrition.json`, `data/class_labels/food_classes.yaml`
- Subdirectories: `class_labels/`, `nutrition_db/`, `raw/`

**`misc/`:**
- Purpose: Human-authored redesign notes and future architecture guidance
- Contains: markdown plans plus a Mermaid diagram
- Key files: `misc/ARCHITECTURE.md`, `misc/revised_implementationplan.md`
- Subdirectories: none in the current worktree

## Key File Locations

**Entry Points:**
- `backend/main.py` - FastAPI application bootstrap
- `frontend/src/main.tsx` - React mount point
- `ml/train_yolo.py` - Detection model training entry
- `scripts/setup_db.py` - Database creation / seeding script

**Configuration:**
- `requirements.txt` - Python packages
- `frontend/package.json` - Frontend scripts and dependencies
- `frontend/vite.config.ts` - Vite configuration
- `frontend/eslint.config.js` - Frontend lint rules
- `configs/yolo_train.yaml` and `configs/portion_model.yaml` - Training configs

**Core Logic:**
- `ai_engine/coordinator.py` - Inference workflow orchestration
- `backend/routes/` - HTTP endpoints
- `backend/models/` - Database tables
- `frontend/src/pages/` - Route-level UI

**Documentation:**
- `README.md` - Project overview and local run instructions
- `misc/ARCHITECTURE.md` - Proposed future architecture
- `misc/revised_implementationplan.md` - Retraining-focused implementation plan

## Naming Conventions

**Files:**
- Python modules use `snake_case.py`
- React components and pages use `PascalCase.tsx`
- API/helper modules use lower-case names like `food.ts`, `meals.ts`, `client.ts`

**Directories:**
- Mostly lower-case singular/plural names by domain (`backend/routes`, `frontend/components`, `ai_engine/models`)
- `__init__.py` is used for Python package boundaries and lightweight export surfaces

**Special Patterns:**
- `main.py` and `App.tsx` act as entry points
- `index.css` and `index.html` hold frontend shell/bootstrap assets

## Where to Add New Code

**New API route:**
- Definition: `backend/routes/`
- Request/response schema: `backend/schemas/`
- Persistence changes: `backend/models/` and possibly `backend/services/`

**New frontend feature:**
- Page: `frontend/src/pages/`
- Shared UI: `frontend/src/components/`
- Network wrapper: `frontend/src/api/`

**New ML / inference capability:**
- Runtime inference logic: `ai_engine/`
- Offline training and experiments: `ml/`
- Static config/data: `configs/` and `data/`

## Special Directories

**`.planning/codebase/`:**
- Purpose: Generated GSD codebase map
- Source: Created by this mapping workflow
- Committed: Intended to be committed when planning docs are tracked

**`data/raw/`:**
- Purpose: Raw dataset assets for retraining work
- Source: User-managed local data
- Committed: currently untracked in the worktree

**`misc/`:**
- Purpose: Transition-state design notes
- Source: Human-authored planning documents
- Committed: Yes, and important for understanding the current branch direction

---
*Structure analysis: 2026-04-11*
*Update when the repo layout changes or the current restructure lands*
