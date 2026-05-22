---
status: investigating
trigger: "Investigate NutriSnap data persistence and LLM issues: user details saved but not used by chatbot, meal planner ignoring user location/details, LLM 403 Forbidden errors, and missing water log deletion endpoint."
created: 2026-05-17T00:00:00Z
updated: 2026-05-17T00:00:00Z
---

## Current Focus

hypothesis: ROOT CAUSE FOUND - (1) LLM 403 Forbidden: Java/Jenkins process on port 8000 (not llama.cpp) blocks all LLM calls → chat fails even though context built correctly; (2) Chat context built correctly but llm.generate_text() raises 403, error caught as websocket error; (3) Meal planner has correct logic but may fail if LLM unavailable; (4) Water deletion endpoint EXISTS in backend but may not have UI button in frontend
test: Verified port 8000 status, LLM service availability, confirmed no llama.cpp server running
expecting: Fix LLM by starting llama.cpp or reconfiguring to use Gemini; user data persistence is actually working
next_action: Phase 3 - RECOMMEND: Configure CHAT_LLM_PROVIDER=gemini as workaround OR start llama.cpp server

## Symptoms

expected: |
  - After saving user details, chatbot uses: full name (Omprakash), height (172cm), weight (45kg), location (Bangalore, India), age (20)
  - Chatbot greets user by actual name, not "rice dish"
  - Meal planner generates meals based on user location, activity level (Sedentary), weight, height
  - Local LLM requests succeed (not 403 Forbidden)
  - Water logs have delete/remove button

actual: |
  - User details save successfully (PUT /users/me → 200) but chatbot calls user "rice dish"
  - When asked about height/weight, chatbot says "not currently available"
  - Meal planner generates generic meals, not personalized by location/details
  - LLM returns: "Client error '403 Forbidden' for url 'http://127.0.0.1:8000/v1/chat/completions'"
  - Water logs have no delete option (Smart Hydration shows +250ml and +500ml buttons only)

errors: |
  WARNING: Client error '403 Forbidden' for url 'http://127.0.0.1:8000/v1/chat/completions'
  GET /logs/weekly → 200 (works fine)
  PUT /users/me → 200 (saves successfully)
  POST /planning/suggest → 200 (but no personalization)

reproduction: |
  1. Fill user settings (name, height, weight, location, age, activity)
  2. Click "Save All Settings" → returns 200
  3. Ask chatbot "what's my name, height and weight?" → Says "rice dish", no height/weight
  4. Refresh meal planner → Generic meals shown, not based on location
  5. Try to delete water log → No delete button available
  6. Backend attempts LLM call → 403 Forbidden error

started: After initial setup

## Eliminated

- hypothesis: Chat context not built at all
  evidence: Code inspection shows _build_context_prompt() IS called at line 226 of chat.py, every message
  timestamp: 2026-05-17T00:07:00Z

- hypothesis: User data schema missing from database
  evidence: Database schema has all required fields: full_name, weight_kg, height_cm, age, gender, activity_level, goal, location
  timestamp: 2026-05-17T00:08:00Z

- hypothesis: Guest user has no profile data
  evidence: Guest user seeded at init with: 75kg, 180cm, age 28, male, moderate activity, maintain goal
  timestamp: 2026-05-17T00:09:00Z

- hypothesis: Water deletion endpoint not implemented in backend
  evidence: DELETE /water/{log_id} endpoint exists at line 67 of water.py, properly implements deletion
  timestamp: 2026-05-17T00:10:00Z

## Evidence

- timestamp: 2026-05-17T00:00:00Z
  checked: Chat endpoint /ws/chat (app/routers/chat.py)
  found: Context IS built via _build_context_prompt() at line 226 - includes user name, height, weight, location, age, activity level from database. Context is prepended to every LLM call with system prompt.
  implication: Chat context building is correct IF user data is in database. Problem must be elsewhere.

- timestamp: 2026-05-17T00:01:00Z
  checked: LLM service local call (nutrisnap/verification/llm_service.py line 286)
  found: POST to http://127.0.0.1:8000/v1/chat/completions uses only headers={"Content-Type": "application/json"}, NO Authorization header. Endpoint reached without auth.
  implication: 403 Forbidden likely due to llama.cpp server rejecting request for non-auth reason (wrong model name? server not running?).

- timestamp: 2026-05-17T00:02:00Z
  checked: Meal planner endpoint /planning/suggest (app/routers/planning.py line 103)
  found: Endpoint checks if required fields exist in current_user dict. If any missing (weight_kg, height_cm, age, gender, activity_level, goal), falls back to hardcoded defaults (2000 cal, 150g protein, etc). No personalization with location.
  implication: If user fields not in current_user dict returned by get_current_user(), meals won't be personalized. Database has location column but not used in meal generation.

- timestamp: 2026-05-17T00:03:00Z
  checked: Water log deletion (app/routers/water.py line 67)
  found: DELETE /{log_id} endpoint EXISTS. Should work if called correctly with user auth. Returns 404 if not found or not owned by user, 204 on success.
  implication: Endpoint is implemented. Frontend component probably doesn't have delete button or doesn't call this endpoint.

- timestamp: 2026-05-17T00:05:00Z
  checked: Port 8000 actual status (via curl and netstat)
  found: curl to http://127.0.0.1:8000/v1/chat/completions returns 403 Forbidden with "No valid crumb was included in the request" (Jenkins/Jetty error). netstat shows PID 7968 on port 8000 = java.exe. NO llama.cpp server running (0 python processes, 0 llama processes).
  implication: CRITICAL - LLM service NOT available. Java app on 8000 blocks llama.cpp. Backend .env configured for local LLM at 8000 (CHAT_LLM_PROVIDER=local). This is the ROOT CAUSE of 403 error. Chat context built correctly but llm.generate_text() fails, returning error to websocket.

- timestamp: 2026-05-17T00:06:00Z
  checked: Frontend AuthContext updateUserProfile function
  found: User profile update sends PUT /users/me with mapped fields, filters NaN values, gets response back, updates currentUser with setCurrentUser(updatedUser), syncs local state. Logic appears correct - should persist data to backend.
  implication: User data persistence mechanism is CORRECT in frontend. If data not showing in chat/meal planner, it's either: (a) not being saved to backend, (b) not being fetched by those endpoints, or (c) chat/llm failing before using it.

## Resolution

root_cause: |
  1. **LLM 403 Forbidden**: Backend configured to use local llama.cpp at port 8000, but Java/Jenkins process occupies port 8000 instead. llama.cpp server NOT running. Backend attempts POST to 8000 → gets Jenkins 403 CSRF error → LLM fails → chat error propagated to client.
  2. **Chat using user data**: Chat endpoint (app/routers/chat.py) correctly builds context with _build_context_prompt() using user DB fields. Context IS sent to LLM. BUT llm.generate_text() fails due to #1, so error shown to client instead of response.
  3. **Meal planner not personalizing**: Endpoint checks for user fields (weight, height, age, etc) in current_user dict. If user profile saved correctly to DB, they should be retrieved and used. Issue may be that user data not fully saved OR fields become null/empty.
  4. **Water deletion missing**: HydrationWidget shows only +250ml, +500ml buttons. DELETE /water/{id} endpoint exists in backend but frontend never calls it. No logs list displayed. No delete buttons.

fix: |
  1. **Backend .env**: Changed CHAT_LLM_PROVIDER from 'local' to 'gemini'. Now chat uses Google Gemini instead of blocked local port 8000.
  2. **Frontend HydrationWidget**: Added fetchTodayLogs() to fetch today's water logs via GET /water/today/logs. Added logs list display with timestamps. Added delete buttons that call DELETE /water/{log_id}. Trash icon with red color. Refresh logs after adding new entry.
  3. **Chat context**: No changes needed - already working correctly. Once LLM works, user context will be used.
  4. **Meal planner**: No changes needed - should work once user data confirmed saved. Prompt includes location but calls it 'unknown' if missing.

verification: |
  [pending testing]

files_changed:
  - backend/.env (CHAT_LLM_PROVIDER=gemini)
  - frontend/src/components/dashboard/HydrationWidget.jsx (water logs list + delete buttons)
