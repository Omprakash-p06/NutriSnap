# External Integrations

**Analysis Date:** 2025-05-15

## APIs & External Services

**AI / LLM:**
- Gemini (Google) - Primary multi-modal reasoning and nutritional analysis
  - SDK/Client: `google-generativeai`
  - Auth: `GEMINI_API_KEY`
- Hugging Face Hub - Model weight hosting
  - Used for: OWL-ViT, SAM 2, GLPN
  - Client: `transformers` / `huggingface_hub`

**Food Database:**
- OpenFoodFacts - Ingredient and nutritional data lookup
  - SDK/Client: `openfoodfacts`

## Data Storage

**Databases:**
- MongoDB Atlas - User profiles and meal history (Noted in STACK.md, but `aiosqlite` also present in `requirements.txt`)
- Local Filesystem - Used for `food_database.json` and `ingredients.csv`

**File Storage:**
- Local filesystem - Temporary uploads in `backend/datasets/uploads/`

**Caching:**
- DiskCache - Persistent caching for API responses and model results
  - Client: `diskcache`

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based authentication
  - Implementation: `backend/app/auth.py` using `python-jose` and `passlib`

## Monitoring & Observability

**Error Tracking:**
- None detected (Local logging only)

**Logs:**
- Loguru - Structured logging in the backend

## CI/CD & Deployment

**Hosting:**
- Docker-based deployment

**CI Pipeline:**
- GitHub Actions (`.github/workflows/`)

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY`
- `SKIP_AI_INIT` (boolean)
- `LLM_PROVIDER` (`cloud` or `local`)

**Secrets location:**
- `.env` files (not committed)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

---

*Integration audit: 2025-05-15*
