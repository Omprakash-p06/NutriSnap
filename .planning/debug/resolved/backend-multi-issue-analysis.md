---
status: resolved
trigger: "Investigate the root causes of three issues in the backend."
created: 2026-05-20T04:55:00Z
updated: 2026-05-20T05:15:00Z
---

## Current Focus

hypothesis: Found root causes for all three issues.
test: N/A (Investigation complete)
expecting: N/A
next_action: Finalize report and archive session.

## Symptoms

expected: 
1. Meal suggestions should work without LLMService attribute errors.
2. Water logging should return a valid response containing the 'amount' field.
3. Water log deletion should find the record and return a 200/204 status.

actual:
1. `ERROR | Meal suggestion failed: 'LLMService' object has no attribute 'prompt'`
2. `ResponseValidationError: 1 validation error: {'type': 'missing', 'loc': ('response', 'amount'), 'msg': 'Field required', 'input': {'id': 49, 'user_email': 'guest@nutrisnap.ai', 'timestamp': '2026-05-20 04:52:14', 'amount_ml': 250}}`
3. `DELETE /water/1779252734708 → 404 Not Found`

errors: 
- LLMService attribute 'prompt' missing
- Water response missing 'amount' (it has 'amount_ml')
- Water deletion 404 for specific ID

reproduction: 
1. Trigger meal suggestion (POST /planning/suggest).
2. Log water (POST /water/).
3. Delete a water log entry (DELETE /water/{id}).

started: 2026-05-20

## Eliminated

## Evidence

- timestamp: 2026-05-20T05:00:00Z
  checked: backend/app/routers/planning.py and backend/nutrisnap/verification/llm_service.py
  found: planning.py calls `llm.prompt(prompt)` but `LLMService` only has `generate_text` and `generate_json`.
  implication: Issue 1 is caused by a method name mismatch and calling an async method synchronously.

- timestamp: 2026-05-20T05:05:00Z
  checked: backend/app/routers/water.py and backend/app/schemas.py
  found: `WaterLogOut` expects `amount`, but the database query returns `amount_ml`.
  implication: Issue 2 is caused by field name mismatch in the response model.

- timestamp: 2026-05-20T05:10:00Z
  checked: frontend/src/components/dashboard/HydrationWidget.jsx
  found: Frontend uses `Date.now()` as `tempId` and only refreshes logs if `POST /water/` succeeds.
  implication: Issue 3 is a cascading failure from Issue 2; the frontend tries to delete a temporary ID that was never synced to the database.

## Resolution

root_cause: 
1. **Meal Suggestions:** `planning.py` incorrectly calls a non-existent `prompt` method on `LLMService`. It should use `await llm.generate_text(prompt)` or `generate_json`.
2. **Water Logging:** Field name mismatch. The database uses `amount_ml` while the Pydantic `WaterLogOut` schema requires `amount`.
3. **Water Deletion:** Cascading error. The `POST` failure prevents the frontend from replacing its temporary timestamp-based ID with a real database ID. The subsequent `DELETE` call uses the timestamp, which doesn't exist in the DB.

fix: 
1. Update `planning.py` to use `await llm.generate_json(prompt)`.
2. Update `water.py` to map `amount_ml` to `amount` or update the schema/database to be consistent.
3. Fix the `POST` issue to resolve the `DELETE` 404.

verification: 
files_changed: []
