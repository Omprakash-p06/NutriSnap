# Debug Session: backend-port-access-forbidden

## Symptoms
- **Actual behavior**: Running `uvicorn app.main:app --reload` fails with `[WinError 10013]`.
- **Error message**: `An attempt was made to access a socket in a way forbidden by its access permissions`
- **Reproduction**: Run backend server on default port 8000.

## Hypotheses
1. **Port in use**: Another process is using port 8000.
2. **Restricted port**: Port 8000 is in a restricted range on this Windows machine (common with Hyper-V).

## Investigation
- Frontend `vite.config.js` is already configured to proxy `/api` to `http://localhost:5000`.
- Backend `app/main.py` is configured to run on port 8000 in its `__main__` block.
- Confirmed mismatch between frontend expectation (5000) and backend default (8000).

## Root Cause
Port 8000 is unavailable on the host machine. The frontend is already expecting port 5000.

## Fix
Change backend port to 5000 to match frontend proxy and avoid the port 8000 conflict.

## Verification
1. Modify `backend/app/main.py` to use port 5000.
2. Run backend with `uvicorn app.main:app --reload --port 5000`.
