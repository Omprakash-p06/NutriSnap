---
status: investigating
trigger: "Investigate and fix system-wide startup failure."
created: 2024-05-14T10:00:00Z
updated: 2024-05-14T10:00:00Z
---

## Current Focus

hypothesis: The garbled output and startup failure are caused by subprocesses (specifically llama_cpp.server) interfering with the terminal session or writing binary/incompatible data to inherited stdout/stderr.
test: Examine start.py and local_llm_backend.py to understand how processes are launched and how logs are handled. Try to run components individually.
expecting: Identification of the specific process causing the garbled output and fixing its log handling.
next_action: Examine start.py and backend/app/services/local_llm_backend.py.

## Symptoms

expected: Normal startup logs for llama.cpp, Backend (Uvicorn), and Frontend (Vite); App reachable at http://localhost:5173.
actual: Garbled output, missing logs, unreachable frontend.
errors: Strange characters like `♪◙` in terminal.
reproduction: Run `python start.py`.
started: Occurred after "fixing" the DLL and log inheritance issues.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
