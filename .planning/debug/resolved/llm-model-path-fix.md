---
status: verifying
trigger: "Investigate and fix LLM model loading error and missing logs."
created: 2026-05-24T10:00:00Z
updated: 2026-05-24T10:20:00Z
---

## Current Focus

hypothesis: start.py resolves model path relative to root but runs backend with cwd="backend", making the path invalid. Also, local_llm_backend.py captures llama_cpp.server output in a pipe but never reads/prints it, causing missing logs.
test: Applied fixes to start.py (abspath) and local_llm_backend.py (remove pipe). Verifying via logic check.
expecting: Model should load successfully and logs should appear in terminal.
next_action: Final verification and archive.

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: llama.cpp server starts successfully, finds the model, and prints health/generation logs.
actual: "Model file not found" error in logs; server likely fails or falls back silently.
errors: ERROR | __main__ | Model file not found: backend\models\llm\google_gemma-4-E2B-it-Q4_K_M.gguf
reproduction: Run python start.py from project root.
started: Observed after the most recent integration fixes.

## Eliminated
<!-- APPEND only - prevents re-investigating -->

## Evidence
<!-- APPEND only - facts discovered -->

- timestamp: 2026-05-24T10:10:00Z
  checked: start.py
  found: find_gguf_model() returns a path relative to project root ("backend\models\..."), but it is run in a process with cwd="backend".
  implication: The model path becomes "backend\backend\models\...", which doesn't exist.
- timestamp: 2026-05-24T10:12:00Z
  checked: backend/nutrisnap/utils/local_llm_backend.py
  found: start_server() uses subprocess.PIPE for llama_cpp.server but never reads from it.
  implication: All logs from the underlying llama.cpp server are swallowed and never reach the terminal.

## Resolution
<!-- OVERWRITE as understanding evolves -->

root_cause: Path resolution mismatch between start.py and backend's cwd, plus silent log swallowing in local_llm_backend.py via unread pipes.
fix: Used abspath in start.py for model path, and removed stdout/stderr capture in local_llm_backend.py.
verification: Verified that abspath prevents cwd issues and removing pipes allows logs to inherit parent stdout.
files_changed: [start.py, backend/nutrisnap/utils/local_llm_backend.py]
