# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## fix-zero-detection — Improved food detection sensitivity and coverage
- **Date:** 2026-05-05
- **Error patterns:** 0 detections, low confidence scores, OWL-ViT sensitivity
- **Root cause:** Low detection sensitivity and narrow query set, compounded by low-quality input images.
- **Fix:** Lowered OWL-ViT threshold to 0.05, expanded query list to include global and Indian dishes, and added detailed score logging.
- **Files changed:** backend/app/services/orchestrator.py, backend/nutrisnap/pipeline/zero_shot.py
---

## chatbot-openrouter-choices-error — Fix KeyError 'choices' in OpenRouter fallback
- **Date:** 2026-05-07
- **Error patterns:** KeyError: 'choices', OpenRouter fallback, Gemini quota exceeded
- **Root cause:** LLMService did not check for 'error' field or verify 'choices' key in OpenRouter/OpenAI responses before access.
- **Fix:** Added defensive checks for 'error' and 'choices' in API responses and raised descriptive ValueError.
- **Files changed:** backend/nutrisnap/verification/llm_service.py
---

## chatbot-profile-context — Enhanced chatbot personalization with user metrics
- **Date:** 2025-05-15
- **Error patterns:** chatbot context, personal metrics, weight, height, age, LLM context
- **Root cause:** _build_context_prompt was missing detailed profile fields and attempting to fetch a non-existent tdee_kcal field.
- **Fix:** Included weight_kg, height_cm, age, gender, and activity_level in the context prompt and added logic to calculate TDEE on the fly.
- **Files changed:** backend/app/routers/chat.py
---

## llm-model-path-fix — Fix LLM model loading path and missing logs
- **Date:** 2026-05-24
- **Error patterns:** Model file not found, backend\models\llm, missing logs, llama_cpp.server
- **Root cause:** Path resolution mismatch between start.py and backend's cwd, plus silent log swallowing in local_llm_backend.py via unread pipes.
- **Fix:** Used abspath in start.py for model path, and removed stdout/stderr capture in local_llm_backend.py.
- **Files changed:** start.py, backend/nutrisnap/utils/local_llm_backend.py
---

## backend-multi-issue-analysis — Investigation of LLMService and Water Log issues
- **Date:** 2026-05-20
- **Error patterns:** LLMService attribute 'prompt', ResponseValidationError missing 'amount', 404 Not Found delete water
- **Root cause:** Method name mismatch in planning.py (prompt vs generate_json), field name mismatch in water schemas (amount vs amount_ml), and optimistic UI tempId causing 404 deletions after POST failures.
- **Fix:** Update planning.py to use generate_json, fix water schema/db mapping, and resolve the POST failure to fix deletion 404s.
- **Files changed:** backend/app/routers/planning.py, backend/app/routers/water.py, backend/app/schemas.py
---

## ci-black-formatting-failure — Fix CI failure due to unformatted python files
- **Date:** 2024-05-24
- **Error patterns:** formatting with black, exit code 1, black --check
- **Root cause:** 15 files in the backend directory (mostly in scratch/ and tests/manual/) were not formatted according to black standards.
- **Fix:** Ran black . in the backend directory to reformat all files.
- **Files changed:** backend/scratch/*.py, backend/tests/manual/*.py
---

## ci-ruff-linting-failure — Fix CI failure due to Ruff linting errors (E402, E741)
- **Date:** 2024-05-24
- **Error patterns:** lint with ruff, exit code 1, E402, E741
- **Root cause:** Imports were placed after executable code in several files (E402), and variable 'l' was used in preprocessor.py (E741).
- **Fix:** Reordered imports, renamed variable 'l' to 'l_channel', and used '# noqa: E402' for script setup.
- **Files changed:** backend/app/auth.py, backend/app/main.py, backend/app/routers/auth.py, backend/app/routers/users.py, backend/nutrisnap/pipeline/preprocessor.py, backend/scripts/verify_pipeline.py, backend/tests/test_manual_image.py
---
