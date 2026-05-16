---
status: investigating
trigger: "ChatBot not working, /ws/chat returns 404, backend shows WebSocket library missing"
created: 2026-05-07T00:00:00Z
updated: 2026-05-07T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_and_recommend_fix
---

## Current Focus

hypothesis: uvicorn running without WebSocket library support (wsproto or websockets not installed)
test: check requirements.txt and installed packages; verify uvicorn installation
expecting: will find WebSocket dependency missing from requirements or not installed
next_action: verify current environment dependencies

## Symptoms

expected: ChatBot WebSocket connection succeeds, messages can be sent and received in real-time.

actual: 
- ChatBot shows "Offline" status
- Cannot send messages
- `/ws/chat` endpoint returns 404
- Backend logs: "No supported WebSocket library detected"

errors: 
```
WARNING:  Unsupported upgrade request.
WARNING:  No supported WebSocket library detected. Please use "pip install 'uvicorn[standard]'", or install 'websockets' or 'wsproto' manually.
INFO:     127.0.0.1:53107 - "GET /ws/chat?token=guest-token HTTP/1.1" 404 Not Found
```

reproduction: 
1. Start backend with `python start.py`
2. Open frontend ChatBot
3. Try to send a message
4. Observe 404 error in backend logs

timeline: Just emerged after wiring ChatBot component to Home.jsx. Was never tested before.

evidence:
- Backend warning explicitly states: "No supported WebSocket library detected"
- uvicorn is running without WebSocket support
- `/ws/chat` route exists in code (backend/app/routers/chat.py line 62: `@router.websocket("/ws/chat")`)
- Route is not being mounted because uvicorn lacks WebSocket capability

## Eliminated

## Evidence

- timestamp: 2026-05-07T00:00:01Z
  checked: Error message and symptoms
  found: Error message is explicit - uvicorn needs WebSocket library installed
  implication: This is a dependency issue, not a code issue

- timestamp: 2026-05-07T00:00:02Z
  checked: backend/requirements.txt
  found: fastapi, uvicorn listed; websockets and wsproto NOT listed
  implication: WebSocket library dependency is missing from requirements

- timestamp: 2026-05-07T00:00:03Z
  checked: backend/app/routers/chat.py line 62
  found: @router.websocket("/ws/chat") properly defined with auth and protocol handling
  implication: Code is correct; problem is not in route implementation

## Resolution

root_cause: Missing WebSocket library dependency. uvicorn requires either 'websockets' or 'wsproto' (or use 'uvicorn[standard]' extra) to handle WebSocket upgrade requests. The library is not installed, causing uvicorn to reject WebSocket connections with 404.

fix: Add 'websockets' to backend/requirements.txt and run 'pip install -r requirements.txt' (or 'pip install uvicorn[standard]' as a single-package alternative)

verification: After installing, backend will recognize WebSocket connections and /ws/chat endpoint will work

files_changed: [backend/requirements.txt]
