# External Integrations

**Analysis Date:** 2026-04-18

**Mapping basis:** This audit covers the active external services and local data dependencies used by the current modular architecture.

## APIs & External Services

**LLM Support (Google Gemini):**
- **Service:** Google Generative AI API.
- **Integration:** `src/nutrisnap/pipeline/fallback.py` uses Gemini to provide nutritional estimates when local models have low confidence.
- **Auth:** Requires `GOOGLE_API_KEY` in environment variables.

**Nutrition Database (USDA):**
- **Service:** USDA FoodData Central API.
- **Integration:** `src/nutrisnap/verification/usda_service.py` provides validation of AI-predicted nutrition values against official government data.
- **Auth:** Requires `USDA_API_KEY` in environment variables.

**Dataset Acquisition (Kaggle):**
- **Library:** `kagglehub`.
- **Integration:** Used in `scripts/ingest_nutrition5k.py` to automatically download the Nutrition5k dataset.
- **Auth:** Requires local Kaggle API credentials.

**Model Hubs (Hugging Face):**
- **Integration:** `transformers` library automatically downloads depth estimation weights (Depth Anything V2) and other model assets on first use.

## Data Storage

**Database:**
- **SQLite:** Used for tracking prediction jobs and results.
- **Client:** `aiosqlite` for asynchronous access in `src/nutrisnap/api/store.py`.
- **Schema:** Managed in the `initialize()` method of `ResultStore`.

**Filesystem:**
- **Image Uploads:** Stored in `data/uploads/` during processing.
- **Processed Data:** Stored in `data/processed/` for training.
- **Model Checkpoints:** Stored in `models/checkpoints/`.

## Monitoring & CI/CD

**GitHub Actions:**
- **Workflows:** `.github/workflows/lint.yaml` (Code quality) and `.github/workflows/test.yaml` (Unit/Integration tests).
- **Trigger:** On push and pull requests.

## Monitoring & Observability

**Logging:**
- Standardized logging to console; can be configured for file output.
- No current integration with external logging platforms (e.g., Sentry, ELK).

**Health Checks:**
- Root endpoint `/` in `src/nutrisnap/api/main.py` serves as a basic health check.

## Integration Gaps & Future Work

- **Cloud Storage:** Current setup relies on local storage; future work may integrate AWS S3 or Google Cloud Storage for image and checkpoint persistence.
- **Auth Provider:** No integration with external identity providers (OAuth, Auth0) currently exists.
- **Real-time Monitoring:** Lack of Prometheus/Grafana or similar dashboards for monitoring inference performance in real-time.

---
*Integration audit: 2026-04-18*
