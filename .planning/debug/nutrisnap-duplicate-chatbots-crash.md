---
status: awaiting_human_verify
trigger: "Investigate NutriSnap multi-issue report: duplicate chatbots, missing input textbox, user settings not persisting, StreakModal crash, and LLM port mismatch."
created: 2026-05-17T00:00:00Z
updated: 2026-05-17T00:30:00Z
---

## Current Focus

hypothesis: 4 independent issues: (1) LLM port hardcoded wrong, (2) StreakModal missing dependency, (3) User schema validation failing on PUT, (4) ChatBot possibly rendering twice
test: Code inspection revealed: LLM .env has 8008 instead of 8000; StreakModal missing calculateStreak in deps; investigating user schema
expecting: All 4 issues fixable with targeted changes
next_action: Fix LLM port, StreakModal deps, then verify ChatBot rendering

## Symptoms

expected: |
  - Single functional chatbot with input textbox
  - User settings save successfully via PUT /users/me
  - User profile data persists in database
  - StreakModal renders without errors
  - LLM connects to correct port (8000)

actual: |
  - Two chatbot instances visible in screenshots
  - One chatbot doesn't have input textbox (appears broken/duplicate)
  - PUT /users/me returns 422 Unprocessable Content
  - Asked about height/weight after saving but data wasn't stored
  - Browser error: "calculateStreak is not a function" in StreakModal.jsx:15
  - LLM warning tries port 8008 instead of 8000

errors: |
  Uncaught TypeError: calculateStreak is not a function
  StreakModal StreakModal.jsx:15
  React error boundary triggered
  
  PUT /users/me → 422 (6.7ms) - multiple times
  
  WARNING: Local LLM not reachable at http://127.0.0.1:8008/v1
  (but server running on 8000)

reproduction: |
  - Load dashboard → see two chatbot panels
  - Try to use chat in right panel → missing input box
  - Update user profile in settings → 422 error, data not saved
  - Ask chatbot about profile → old data returned
  - Check browser console → StreakModal crash error

started: After previous chatbot/dock fixes

## Eliminated

## Evidence

- timestamp: phase1
  checked: backend/.env LLM configuration
  found: LOCAL_LLM_URL=http://127.0.0.1:8008/v1 and LLAMA_PORT=8008
  implication: Server running on 8000, but env points to 8008 - connection fails with "not reachable" warning

- timestamp: phase1
  checked: frontend useMealHistory.js and StreakModal.jsx
  found: calculateStreak IS exported from useMealHistory (line 168) and async function defined (line 121), BUT StreakModal useEffect missing calculateStreak dependency
  implication: React rule violated; useEffect depends on calculateStreak but not in deps array - could cause stale closures

- timestamp: phase1  
  checked: ChatBot component and App.jsx rendering logic
  found: ChatBot rendered in 3 locations - Home.jsx (legacy, unused), ChatPage.jsx (fullPage mode), App.jsx (floating when activeTab !== chat)
  implication: When activeTab === "chat", only ChatPage's ChatBot should show. Floating ChatBot hidden by condition. Seems correct but need to verify

- timestamp: phase1
  checked: backend/app/routers/users.py PUT /me endpoint
  found: Update endpoint uses dynamic SQL and filters None values, UserUpdate schema looks correct
  implication: 422 error likely due to frontend sending invalid data or missing required fields in request body

## Resolution

root_cause: |
  1. **LLM Port Mismatch**: .env configured to use port 8008 but server running on 8000 → connection fails with "not reachable" warning
  2. **StreakModal crash**: Missing dependency in useEffect - calculateStreak called but not listed in deps array, violates React rules
  3. **User Profile 422 Error**: Frontend sends NaN values when numeric fields (age, weight, height) are empty, FastAPI schema rejects NaN
  4. **Duplicate Chatbots**: Rendering logic appears correct (mutually exclusive conditions), may resolve after other fixes

fix: |
  1. Changed .env: LOCAL_LLM_URL from 8008 to 8000 and LLAMA_PORT from 8008 to 8000
  2. Added calculateStreak to StreakModal useEffect dependency array
  3. Modified AuthContext updateUserProfile to filter NaN values before sending to backend
  4. Verified ChatBot rendering logic is correct - no changes needed yet

verification: |
  [pending user test]

files_changed:
  - backend/.env (LLM_URL and LLAMA_PORT ports)
  - frontend/src/components/StreakModal.jsx (dependency array)
  - frontend/src/context/AuthContext.jsx (NaN filtering)
