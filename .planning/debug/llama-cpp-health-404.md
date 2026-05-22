---
status: diagnosed
trigger: "Investigate issue: llama-cpp-health-404"
created: 2025-01-24T12:00:00Z
updated: 2025-01-24T12:00:00Z
---

## Current Focus

hypothesis: llama.cpp server uses a different health check endpoint or is misconfigured.
test: Check how llama.cpp is started and what endpoints it exposes.
expecting: Identify the correct health endpoint or a configuration error.
next_action: gather initial evidence

## Symptoms

expected: http://127.0.0.1:8008/health should return a successful status (200 OK).
actual: http://127.0.0.1:8008/health returns 404 Not Found.
errors: "llama.cpp server did not become healthy within 60s" in backend logs.
reproduction: Run `python start.py`.
started: Observed in the current session logs.

## Eliminated

## Evidence

- timestamp: 2025-01-24T12:15:00Z
  checked: backend/nutrisnap/utils/local_llm_backend.py
  found: is_server_running() checks http://127.0.0.1:8008/health.
  implication: The health check is hardcoded to use the /health endpoint.

- timestamp: 2025-01-24T12:20:00Z
  checked: llama_cpp.server.app (v0.3.23)
  found: The server defines routes for /v1/completions, /v1/chat/completions, /v1/models, etc., but NO /health route.
  implication: llama_cpp.server does not provide a /health endpoint, causing 404.

- timestamp: 2025-01-24T12:25:00Z
  checked: llama-cpp-python source in site-packages
  found: No mention of "health" in the server source code.
  implication: The endpoint /health is genuinely missing from the third-party server implementation.

## Resolution

root_cause: The `LlamaCppBackend` class in `backend/nutrisnap/utils/local_llm_backend.py` attempts to verify server health by hitting the `/health` endpoint. However, the `llama-cpp-python` server (which powers the local LLM) does not implement a `/health` route, resulting in a 404 Not Found response. This causes `is_server_running()` to return `False`, making the backend believe the server failed to start.
fix: 
verification: 
files_changed: []
