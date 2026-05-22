# Manual / Debug Test Scripts

These scripts were previously in the project root and were used for manual debugging and integration testing during development. They are **not** part of the automated pytest suite.

## Files

| Script | Purpose |
|---|---|
| `test_api.py` | Manual test of the `/predict/` endpoint against a running backend |
| `test_inference.py` | Manual test of the `SequentialOrchestrator` ML pipeline |
| `test_ws.py` | Manual WebSocket chat endpoint test |
| `test_current_state.py` | Debug script to check DLL loading state (Windows-specific) |
| `test_dll_deps.py` | Debug script for llama DLL dependency checks |
| `test_llama_import.py` | Debug import test for llama_cpp |
| `test_minimal_deps.py` | Minimal dependency loading smoke test |
| `reproduce_search.py` | Script to reproduce food search issues |

## Running

These scripts require a running NutriSnap backend. Start the backend first:

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload
```

Then run individual scripts from the project root:

```bash
python backend/tests/manual/test_api.py
```

> **Note:** These are NOT run by CI/CD. Only `backend/tests/` (non-manual) tests run in GitHub Actions.
