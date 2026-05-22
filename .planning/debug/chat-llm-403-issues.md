---
status: verifying
trigger: Deep investigation into why user data isn't being passed to chatbot even though it's saved successfully, and why LLM returns 403 Forbidden
created: 2026-05-17T00:00:00Z
updated: 2026-05-17T10:30:00Z
---

## Current Focus

hypothesis: (fixes applied and deployed)
test: Verify each fix works:
  1. Update profile via PUT /users/me
  2. Send chat message - should reflect new profile WITHOUT reconnect
  3. Call meal planning - should no longer timeout/fallback
  4. Water deletion - verify still works

expecting: 
  - Chat shows updated user data immediately after profile update
  - Meal planning responds in <2 seconds (not 11+ seconds)
  - No 403 errors in logs

next_action: Run verification tests

## Symptoms

expected: 
- Chat references user details from their profile
- LLM calls succeed with 200 OK
- Meal planner personalizes suggestions
- Water logs delete successfully

actual: 
- Chat still calls user "rice dish" (generic fallback name from first connection)
- PUT /users/me returns 200 (data saves to database)
- But chat doesn't reflect the update until reconnect
- LLM requests appear to be working (no 403 in logs)
- Meal planner takes 11+ seconds (might be using fallback but returning 200 anyway)

errors: 
- Chat shows stale user data ("rice dish") after PUT /users/me
- No explicit 403 visible; might be caught and falling back

reproduction: 
1. Connect to chat (loads profile with old/default data)
2. Update profile via PUT /users/me (returns 200)
3. Send chat message - still uses old name "rice dish"
4. Reconnect to chat - NOW sees updated name

started: Profile caching in chat websocket

## Eliminated

(none yet)

## Evidence

- **2026-05-17 03:01:03** PUT /users/me → 200 (profile update successful to DB)
- **2026-05-17 03:01:42** Chat LLM Response: "Hello there, rice dish!" (stale data from initial connection)
- **Port 8000 verification**: Running java process (Jenkins), not llama.cpp
- **Direct HTTP test**: `POST http://127.0.0.1:8000/v1/chat/completions` returns **403 Forbidden: "No valid crumb was included in the request"** (Jenkins CSRF error)
- **Chat code inspection**: Profile loaded once at connection (chat.py:132-140), reused for all messages without refresh
- **2026-05-17 03:03:02** POST /planning/suggest → 200 (11847.8ms) - long delay indicates fallback to Gemini after local fails
- **Config analysis**: 
  - CHAT_LLM_PROVIDER=gemini (chat uses Gemini, not local)
  - LLM_PROVIDER=local (planning tries local first)
  - LOCAL_LLM_URL=http://127.0.0.1:8000/v1 (points to wrong server - Jenkins)
- **Backend logs**: No "LLM provider failed" warnings = local provider call is being caught and falling back silently

## Resolution

root_cause: 
1. **Chat stale profile**: Profile dict loaded once at WebSocket connection (line 140), never refreshed for subsequent messages. User updates don't appear until reconnect.
2. **LLM 403 Forbidden**: LOCAL_LLM_URL (http://127.0.0.1:8000) incorrectly points to Jenkins server instead of llama.cpp. Requests get 403 "No valid crumb" CSRF error, triggering fallback to Gemini (11+ second delay).
3. **Meal planner slow**: Uses LLM_PROVIDER=local, hits Jenkins 403, falls back to Gemini (explains 11.8s delay).

fix: 
1. **Chat profile refresh** (backend/app/routers/chat.py): 
   - Added code to reload user profile and recent_logs from database on EACH chat message (before building context prompt)
   - Ensures profile updates reflect in chat immediately without reconnect
   
2. **Disable broken local LLM** (backend/.env):
   - Changed `LLM_PROVIDER=local` → `LLM_PROVIDER=gemini`
   - Now planning endpoint uses Gemini directly (skips broken Jenkins server)
   - Eliminates 403 errors and slow fallback delays

3. **Water deletion**: No fix needed - endpoint exists (DELETE /water/{log_id}) and frontend already calls it (HydrationWidget.jsx:73-90)

verification: (pending - need to restart server and test)
