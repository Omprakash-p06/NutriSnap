---
status: investigating
trigger: "Investigate and fix chatbot issues. WebSocket connection failure and placeholder model name 'Gemini 2.0 Flash' in the UI."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:00:00Z
---

## Current Focus

hypothesis: WebSocket failure is due to missing backend dependencies and possibly incorrect routing/proxy configuration. Placeholder model name is hardcoded in the frontend.
test: Check backend dependencies, verify WebSocket route in FastAPI, check Vite proxy config, and search frontend for hardcoded model name.
expecting: Find missing 'websockets' dependency, missing or incorrect /ws/chat route, and hardcoded string in React component.
next_action: Check backend requirements and installed packages.

## Symptoms

expected: 
- Chatbot should connect via WebSocket and allow messaging.
- UI should show the actual model name being used by the backend.

actual:
- Chatbot shows "Offline".
- Vite logs show `ws proxy error: Error: write ECONNABORTED`.
- Backend logs show `WARNING: No supported WebSocket library detected. Please use "pip install 'uvicorn[standard]'", or install 'websockets' or 'wsproto' manually.`
- `/ws/chat` returns 404.
- UI shows "Gemini 2.0 Flash" as a static label.

errors:
- `ECONNABORTED` in Vite.
- `404 Not Found` for `/ws/chat`.
- `No supported WebSocket library detected` in Backend.

reproduction: 
1. Run `python start.py`.
2. Open the chatbot in the frontend.
3. Observe "Offline" status and console errors.

started: Detected after recent integration work.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
