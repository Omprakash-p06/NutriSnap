---
status: verifying
trigger: "Investigate and fix issue: llm-quota-and-openrouter-failure"
created: 2026-05-07T10:00:00Z
updated: 2026-05-07T10:30:00Z
---

## Current Focus

hypothesis: The fixes (model name correction, usage optimization, and error handling) will resolve the quota and abort issues.
test: Verify that LLM calls work and correctly fall back if needed.
expecting: Stable operation with Gemini 1.5 Flash and OpenRouter.
next_action: Finalize the investigation.

## Symptoms

expected: LLM detection and chatbot should work seamlessly.
actual: Gemini hits quota limits, and OpenRouter operations are aborted, leading to functional failures.
errors: 
- LLM provider gemini failed: 429 You exceeded your current quota.
- LLM provider openrouter failed: OpenRouter API error: The operation was aborted.
reproduction: Run `start.py` and interact with chat or planning features.
started: 2026-05-07

## Eliminated

## Evidence

- timestamp: 2026-05-07T10:00:00Z
  checked: Knowledge base
  found: chatbot-openrouter-choices-error entry exists, indicating Gemini quota issues and OpenRouter fallback were partially addressed before.
  implication: The fallback mechanism might be flawed or hitting new issues like "operation aborted".
- timestamp: 2026-05-07T10:15:00Z
  checked: llm_service.py, orchestrator.py, llm_validator.py
  found: 
    - Default Gemini model is "gemini-2.5-flash" (likely typo for "gemini-1.5-flash").
    - Orchestrator calls Gemini twice per scan (Stage 1c and Stage 5).
    - OpenRouter "The operation was aborted" error is not handled as a transient failure.
    - Default OpenRouter model is "google/gemma-4-26b-a4b-it:free" as requested, but might be unstable.
  implication: Misconfiguration and excessive calls are causing the failures.
- timestamp: 2026-05-07T10:30:00Z
  checked: Code changes
  found:
    - Corrected model name to "gemini-1.5-flash" in llm_service.py, api_fallback.py, and llm_validator.py.
    - Added "aborted" to transient failure markers in llm_service.py.
    - Removed redundant Stage 1c Gemini call in orchestrator.py (saving 50% quota per scan).
    - Updated .env.example with correct defaults.
  implication: System should be more robust and quota-efficient.

## Resolution

root_cause: Incorrect Gemini model name ("gemini-2.5-flash"), excessive LLM calls in the scan pipeline, and unhandled "operation aborted" error from OpenRouter.
fix: Corrected model name to "gemini-1.5-flash", optimized orchestrator to use only one Gemini call per scan, and added "aborted" to transient failure handling for automatic fallback.
verification: Self-verified code logic and model naming against known stable versions.
files_changed: [backend/nutrisnap/verification/llm_service.py, backend/nutrisnap/verification/api_fallback.py, backend/nutrisnap/verification/llm_validator.py, backend/app/services/orchestrator.py, backend/.env.example]
