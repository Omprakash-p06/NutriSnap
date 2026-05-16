---
status: resolved
trigger: "Investigate and fix the chatbot failure caused by 'choices' KeyError in OpenRouter fallback when Gemini quota is exceeded."
created: 2025-05-14T10:00:00Z
updated: 2026-05-07T01:21:00Z
---

## Current Focus

hypothesis: OpenRouter response does not contain 'choices' key, likely due to an error response that is not being handled correctly.
test: Examine backend/nutrisnap/verification/llm_service.py to see how OpenRouter responses are handled.
expecting: Find code that accesses ['choices'] without checking if it exists or if the response is an error.
next_action: gather initial evidence

## Symptoms

expected: When Gemini hits its quota, the chatbot should transparently fall back to OpenRouter (or OpenAI) and continue working.
actual: Chatbot displays an error message "⚠ 'choices'" to the user. Backend logs show KeyError: 'choices' during OpenRouter call.
errors: KeyError: 'choices' in backend/nutrisnap/verification/llm_service.py during OpenRouter call.
reproduction: 
1. Ensure Gemini API quota is reached or temporarily sabotage the Gemini API key.
2. Send a message to the chatbot.
3. Observe the 'choices' error in the UI and backend logs.
started: Detected after Gemini free tier quota was reached.

## Eliminated

## Evidence

- timestamp: 2026-05-07T01:19:06Z
  checked: backend/nutrisnap/verification/llm_service.py and reproduction script
  found: Confirmed that _call_openrouter (and _call_openai) raise KeyError: 'choices' if the response from the API is successful (200 OK) but doesn't contain the 'choices' key (e.g., if it contains an 'error' object instead).
  implication: The code needs to be more robust when handling LLM provider responses, checking for errors and the existence of expected keys.

## Resolution

root_cause: The OpenRouter and OpenAI provider calls in LLMService did not check for an 'error' field in the API response or verify the existence of the 'choices' key before accessing it. If the provider returned a 200 OK but with an error body (common in some failure modes), it caused a KeyError: 'choices'.
fix: Added robust checks for 'error' and 'choices' in _call_openrouter and _call_openai methods. Now they raise a descriptive ValueError if the expected structure is missing or an error is returned.
verification: Created reproduction and verification scripts using mocks to simulate Gemini quota failure (429) and OpenRouter error response. Confirmed that the fix correctly catches the error and provides a descriptive message instead of crashing with KeyError.
files_changed: [backend/nutrisnap/verification/llm_service.py]
