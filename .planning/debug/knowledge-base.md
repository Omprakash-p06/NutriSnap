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
