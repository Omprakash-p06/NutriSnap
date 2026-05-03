---
status: resolved
trigger: "Investigate vulnerabilities, problems, and integration gaps in the NutriSnap project. Specifically, verify if the frontend is fully integrated with the intended \"production\" backend (Python)."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:45:00Z
---

## Current Focus

hypothesis: The project suffers from a "split personality" where the frontend is coupled to an insecure Node.js mock backend while a production-grade Python ML backend sits idle.
test: Audit complete.
expecting: Audit results confirmed.
next_action: Return results.

## Symptoms

expected: Frontend should use the production ML backend (Python) with secure JWT auth.
actual: Frontend uses a Node.js "mock-ish" backend with OpenAI and no real auth.
errors: Potential port collision on port 5000.
reproduction: 
- Check frontend/vite.config.js (proxies /api to 5000).
- Check frontend/server/server.js (Node.js server on 5000).
- Check backend/app/main.py (Python server on 5000).
started: New project under development.

## Eliminated


## Evidence

- timestamp: 2025-05-15T10:15:00Z
  checked: vite.config.js, frontend/server/server.js, backend/app/main.py
  found: Both Node.js and Python backends target port 5000. Vite proxies /api to port 5000, which currently hits the Node.js server.
  implication: Port collision exists. Frontend is currently locked into the insecure Node.js backend.

- timestamp: 2025-05-15T10:20:00Z
  checked: frontend/src/services/api.js, frontend/src/hooks/usePrediction.js
  found: authAPI uses fake JWT tokens and hardcoded delays. usePrediction (hook for Python ML) is mostly unused in the main flow (Home.jsx).
  implication: The sophisticated Python ML pipeline is bypassed for a simple OpenAI-based Express implementation.

- timestamp: 2025-05-15T10:25:00Z
  checked: Node.js server endpoints (server.js)
  found: Broken Access Control: endpoints like /api/meals and /api/user/settings trust 'email' from query/body without token verification. /api/meals/:id allows unauthenticated deletion.
  implication: Severe security vulnerability. Any user can access, modify, or delete any other user's data by knowing their email or meal ID.

- timestamp: 2025-05-15T10:30:00Z
  checked: Python backend (app/routers/auth.py, app/routers/prediction.py)
  found: Real JWT auth, rate limiting, and sophisticated async ML pipeline are present but not integrated with the frontend.
  implication: The intended production backend is ready but disconnected.

- timestamp: 2025-05-15T10:40:00Z
  checked: Python backend routers
  found: Missing feature parity for 'water', 'insights', and 'community feed' in Python backend.
  implication: Migration requires porting these features from Node to Python.

## Resolution

root_cause: Parallel development led to an orphaned production backend (Python) and a "temporary" Node.js backend that became the de facto integration point. Port collision on 5000 further obscures the issue.
fix: 
1. Port 'water', 'insights', and 'posts' routers from Node.js to Python FastAPI.
2. Update Frontend AuthContext to use Python's /auth/login and /auth/signup.
3. Update ScanBox and Home.jsx to use usePrediction hook (polling) instead of direct authAPI.scanImage (OpenAI).
4. Remove Node.js server (frontend/server) and change Python port to 8000 (standard) or keep 5000 and update proxy.
verification: Audit complete. Root cause and migration path identified.
files_changed: []
