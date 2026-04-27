# Tech Stack

**Refresh Date:** 2026-04-27

## Core Technologies

### Backend (ML & API)
- **Language:** Python 3.10+
- **API Framework:** FastAPI
- **Asynchronous Runtime:** Uvicorn
- **Database (NoSQL):** MongoDB (via Motor)
- **ML Frameworks:**
  - **PyTorch:** Core deep learning engine.
  - **Ultralytics (YOLOv8):** Multi-food detection.
  - **Transformers (Hugging Face):** ViT (Regression) and GLPN (Depth).
  - **Segment Anything 2 (SAM 2):** Instance segmentation.
- **Data Handling:**
  - **Pillow (PIL):** Image processing.
  - **NumPy / Pandas:** Data manipulation.

### Frontend (PWA)
- **Framework:** React 19
- **Build Tool:** Vite 8
- **Styling & Animations:**
  - **Vanilla CSS:** Modular styling.
  - **Framer Motion:** High-performance animations and micro-interactions.
- **Icons:** Lucide React
- **Charts:** Recharts
- **Authentication:** React OAuth Google
- **PWA Support:** Vite Plugin PWA

## Infrastructure & DevOps
- **Local Development:** Windows-based environment.
- **Version Control:** Git.
- **CI/CD:** GitHub Actions (`.github/workflows/deploy.yml`).
- **Environment Management:** `python-dotenv` (Backend), `.env` (Frontend).

## Development Tools
- **Code Quality:**
  - **Flake8:** Linting.
  - **Pre-commit:** Git hooks for code quality.
  - **ESLint:** Frontend linting.
- **Dependency Management:**
  - `requirements.txt` (Backend)
  - `package.json` (Frontend)
