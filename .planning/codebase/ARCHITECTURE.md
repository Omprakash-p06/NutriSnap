# Architecture

**Analysis Date:** 2026-04-18

**Mapping basis:** This design reflects the modular, multi-stage inference pipeline currently implemented in the `nutrisnap` package.

## Pattern Overview

**Overall:** Modular AI backend with asynchronous background job processing.

**Key Characteristics:**
- **Pipeline Abstraction:** Inference is decomposed into discrete, interchangeable components (Segmentation, Volume Estimation, Nutrition Regression).
- **Async Execution:** Heavy AI tasks are offloaded to background workers to maintain API responsiveness.
- **Hierarchical Config:** Nested YAML files enable fine-grained control over model parameters and system behavior.
- **Verification Loop:** Predictions are cross-referenced with external data (USDA) and sanity rules before finalization.
- **Service Isolation:** Clear separation between API, data, modeling, and utility concerns.

## Layers

**API Layer:**
- Purpose: Entry point for external requests; manages job lifecycle and persistence.
- Components: FastAPI (`src/nutrisnap/api/main.py`), Result Store (`src/nutrisnap/api/store.py`).
- Responsibilities: Validating input, persisting uploads, status reporting.

**Worker / Orchestration Layer:**
- Purpose: Execute and manage the end-to-end inference for a single job.
- Components: `JobWorker` (`src/nutrisnap/api/worker.py`), `InferencePipeline` (`src/nutrisnap/pipeline/inference.py`).
- Responsibilities: Error handling, resource management, result aggregation.

**Inference Pipeline Layer:**
- Purpose: The core logic of food analysis broken into specialized tasks.
- Components:
    - **Segmenter:** Detects and masks individual food items (`src/nutrisnap/pipeline/segmenter.py`).
    - **Volume Estimator:** Calculates physical volume from image/depth data (`src/nutrisnap/pipeline/volume.py`).
    - **Nutrition Regressor:** Predicts macronutrients from features and volume (`src/nutrisnap/models/nutrition_regressor.py`).
    - **Fallback Handler:** Uses LLMs (Gemini) when local models fail (`src/nutrisnap/pipeline/fallback.py`).

**Model Layer:**
- Purpose: Underlying neural network architectures.
- Components: Backbones (EfficientNet, Swin), Fusion modules, Depth CNNs.
- Located in: `src/nutrisnap/models/`

**Data Layer:**
- Purpose: Data ingestion, cleaning, and preparation for both training and inference.
- Components: `NutriSnapDataset`, `DataModule`, Preprocessing scripts.

**Verification Layer:**
- Purpose: Reliability checks for AI outputs.
- Components: `USDAStore`, `RuleValidator`.
- Located in: `src/nutrisnap/verification/`

## Data Flow

**Inference Request Cycle:**
1. **Submission:** Client POSTs image to `/predict`. API saves to `data/uploads/` and creates a `PENDING` job.
2. **Scheduling:** API triggers a background task using `FastAPI.BackgroundTasks`.
3. **Orchestration:** `JobWorker` picks up the task, sets status to `PROCESSING`, and starts the `InferencePipeline`.
4. **Execution:** 
    - Segmenter identifies regions of interest.
    - Volume and depth are estimated for each region.
    - Regressor produces initial nutrition estimates.
    - (Optional) Gemini-based fallback if confidence is low.
5. **Validation:** `RuleValidator` and `USDAService` check the results for consistency.
6. **Completion:** Results are saved to SQLite, status set to `COMPLETED`.
7. **Retrieval:** Client polls `/result/{job_id}` for the final JSON payload.

## Key Abstractions

**Standardized Components:**
- Pipeline modules share a common interface to allow swapping implementations (e.g., different segmenters).

**Result Store:**
- Abstracted persistence for job metadata and outputs, ensuring the API and worker can communicate via a shared database state.

**Unified Config:**
- A single configuration object (loaded from YAML) is passed through the system to ensure consistency.

## Entry Points

**Production API:**
- `src/nutrisnap/api/main.py` - Start with `uvicorn nutrisnap.api.main:app`.

**Training Pipeline:**
- `src/train.py` - Main script for model training and fine-tuning.

**Data Preparation:**
- `scripts/preprocess_full.py` - End-to-end script for preparing datasets from raw formats.

## Error Handling

**Strategy:** Fail gracefully with fallback options and detailed job-level error reporting.

- **Job-level errors:** Captured in the `ResultStore` and reported via the API.
- **Pipeline fallbacks:** If a specific model fails or returns low confidence, the system can trigger a Gemini-based fallback.
- **Sanity checks:** Rule-based validation prevents physically impossible nutrition estimates from being returned.

## Cross-Cutting Concerns

**Logging:**
- Standard Python logging used across all modules with centralized configuration.

**Metrics:**
- Tracking of inference time, model confidence, and prediction accuracy.

**Persistence:**
- Shared SQLite database for job tracking and result archival.

---
*Architecture analysis: 2026-04-18*
