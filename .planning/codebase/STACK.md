# Technology Stack

**Analysis Date:** 2025-05-15

## Languages

**Primary:**
- Python 3.11+ - Backend API and ML inference logic
- JavaScript/TypeScript - Frontend (React)

## Runtime

**Environment:**
- Node.js (Frontend)
- Python 3.11+ (Backend)

**Package Manager:**
- npm - Frontend
- pip (within venv) - Backend
- Lockfile: `package-lock.json` present

## Frameworks

**Core:**
- FastAPI - Backend web framework
- React 18+ (Vite) - Frontend UI
- Tailwind CSS - UI Styling

**Testing:**
- Pytest - Backend testing
- ESLint/Prettier - Frontend linting and formatting

**Build/Dev:**
- Vite - Frontend build tool
- Uvicorn - ASGI server for FastAPI

## Key Dependencies

**Critical:**
- `ultralytics` - YOLOv8 for food detection
- `transformers` - SAM 2, GLPN, and OwlViT models
- `llama-cpp-python` - Local LLM inference (installed via `backend/scripts/setup_local_llm.py`)
- `torch` / `torchvision` - Deep learning framework
- `google-generativeai` - Gemini 2.0 Flash integration

**Infrastructure:**
- `fastapi` - Web API
- `websockets` - Chatbot and real-time communication
- `vite-plugin-pwa` - PWA support for offline usage

## Configuration

**Environment:**
- `.env` files in `backend/` and `frontend/` (copied from `.env.example` by `setup.py`)
- Key configs: `GEMINI_API_KEY`, `SKIP_AI_INIT`, `LLM_PROVIDER`

**Build:**
- `vite.config.js`
- `pyproject.toml`
- `requirements.txt`

## Platform Requirements

**Development:**
- Node.js & npm
- Python 3.11+
- CUDA-compatible GPU (optional but recommended for AI inference)

**Production:**
- Docker (Dockerfile present in both `backend/` and `frontend/`)
- Deployment target: Cloud (Azure/GCP/AWS) or Local Server

---

*Stack analysis: 2025-05-15*
