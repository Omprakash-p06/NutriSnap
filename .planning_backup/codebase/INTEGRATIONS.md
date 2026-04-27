# External Integrations

**Refresh Date:** 2026-04-27

## APIs & External Services

**Google Gemini (LLM):**
- **Service:** Gemini 2.0 Flash (via Google Generative AI SDK).
- **Usage:**
  - `src/nutrisnap/verification/api_fallback.py`: Provides nutritional estimates when local models fail or have low confidence.
  - `src/nutrisnap/verification/llm_validator.py`: Cross-validates local model predictions against visual reasoning.
- **Auth:** `GOOGLE_API_KEY`.

**USDA FoodData Central:**
- **Service:** USDA Standard Reference Legacy API.
- **Usage:** `src/nutrisnap/verification/usda_service.py` validates AI-predicted nutrition values against official government data.
- **Auth:** `USDA_API_KEY`.

**Google OAuth:**
- **Service:** Google Identity Services.
- **Usage:** Frontend authentication via `@react-oauth/google`.
- **Auth:** `VITE_GOOGLE_CLIENT_ID`.

**Hugging Face Hub:**
- **Usage:** Automatic download of model weights for ViT, GLPN, and SAM 2.

## Data Storage

**MongoDB:**
- **Role:** Primary data store for user profiles, meal history, and social feed.
- **Driver:** Motor (Async MongoDB driver).

**Local Filesystem:**
- **Role:** Temporary storage for uploaded images and model checkpoints.

## Dataset Dependencies

**Nutrition5k:**
- **Usage:** Primary training and evaluation dataset.
- **Ingestion:** Managed via `scripts/ingest_nutrition5k.py`.
