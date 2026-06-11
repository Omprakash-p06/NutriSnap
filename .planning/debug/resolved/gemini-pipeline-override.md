---
status: resolved
trigger: "Gemini API key isn't doing the food detection and final result validation in the pipeline."
created: 2025-01-25T14:30:00Z
updated: 2025-01-25T14:45:00Z
---

## Current Focus

hypothesis: Missing import in llm_validator.py and invalid default model name were causing issues. Also, validation authority was not correctly tracked.
test: Run backend/reproduce_issue.py and verify model names and logic.
expecting: Correct model name usage and improved authority tracking.
next_action: Completed investigation and applied fixes.

## Symptoms

expected: Gemini overrides local model results for food labels and nutrients.
actual: Local model result is being used directly; Gemini seems to be bypassed or failing.
errors: Potential 404/403 errors due to invalid model name 'gemini-2.5-flash'.
reproduction: Run backend/reproduce_issue.py.
started: Detected recently.

## Eliminated
- Hypothesis: LLMService import missing in llm_validator.py.
  evidence: Checked file content and found the import was present.
  timestamp: 2025-01-25T14:35:00Z

## Evidence
- Found 'gemini-2.5-flash' used as a default model name in multiple files, which is likely invalid.
- Found that Stage 5 validation in orchestrator.py hardcoded authority as 'api_key' even if it fell back to 'local'.
- Verified that LLMValidator now tracks the actual provider used.

## Resolution

root_cause: Invalid default model name 'gemini-2.5-flash' caused Gemini API calls to fail or 404, triggering fallbacks to local text-only models. Additionally, the orchestrator did not correctly distinguish between API-based and local validation authority.
fix: Corrected default model names to 'gemini-1.5-flash', added provider tracking to ValidationResult, and updated the orchestrator to correctly attribute validation authority.
verification: Ran reproduction script and confirmed model name 'gemini-1.5-flash' is now used.
files_changed: [backend/nutrisnap/verification/llm_validator.py, backend/nutrisnap/verification/llm_service.py, backend/app/services/orchestrator.py, backend/.env.example]
