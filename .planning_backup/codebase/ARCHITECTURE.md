# Architecture Overview

**Refresh Date:** 2026-04-27

## System Design

The NutriSnap platform follows a modular, AI-first architecture split between a high-performance backend and a modern React-based PWA.

### 1. High-Level Architecture
- **Frontend:** React 19 PWA communicating via REST API with the backend.
- **Backend:** FastAPI service orchestrating a multi-stage ML inference pipeline.
- **Database:** MongoDB for persistent storage of user data and meal history.

### 2. ML Inference Pipeline (NutriSnap-Backend)
The core value proposition is delivered through a sequential pipeline:
1. **Multi-Food Detection:** YOLOv8 identifies individual food items in the frame.
2. **Segmentation:** SAM 2 generates high-fidelity masks for each detected item.
3. **Depth Estimation:** GLPN estimates the 3D depth map of the scene.
4. **Volume Estimation:** Geometric algorithms calculate the volume based on masks and depth.
5. **Nutrition Regression:** ViT/EfficientNet models predict calorie and macro density.
6. **LLM Validation:** Gemini 2.0 Flash performs a final "sanity check" on the composite results.

### 3. Backend Workflow
- **API (FastAPI):** Handles image uploads and starts asynchronous jobs.
- **Worker (`worker.py`):** Pulls jobs from the queue and runs the `InferencePipeline`.
- **Result Store (`store.py`):** Manages the lifecycle of prediction results in the database.

### 4. Frontend Architecture
- **View Management:** Dynamic switching between Landing, Dashboard, and Scanning views.
- **State Management:** React Context API for global states (Auth, Theme).
- **Service Layer:** `api.js` centralizes backend communication.
- **PWA Features:** Offline caching and "Add to Home Screen" support.

### 5. Data Flow
1. **User Action:** Captures photo -> Uploads to `/predict`.
2. **Backend Processing:** Starts background job -> Returns `job_id`.
3. **Frontend Polling:** Checks status until "completed".
4. **Result Delivery:** Backend returns nutrition breakdown -> Frontend renders `ResultsCard`.

## Key Design Patterns
- **Pipeline Pattern:** Sequential processing of ML stages with fallback logic.
- **Adapter Pattern:** Wrapping different model architectures (SAM, GLPN) in a consistent interface.
- **Observer Pattern (Frontend):** Real-time UI updates based on auth and meal history changes.
