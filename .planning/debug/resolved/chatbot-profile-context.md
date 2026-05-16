---
status: verifying
trigger: "Enhance chatbot personalization by including more user profile data in the LLM context."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:25:00Z
---

## Current Focus

hypothesis: The fix (calculating TDEE and including profile metrics in the context prompt) will allow the AI to answer personalized questions correctly.
test: Perform manual verification or run a test script that mocks the websocket and user profile.
expecting: AI to use weight, height, etc. in its response without asking for them.
next_action: Create a small verification script to test the context generation logic.

## Symptoms

expected: AI knows the user's personal metrics (weight, height, age, etc.) and uses them to provide specific advice without asking the user to provide them again.
actual: AI asks for weight/height instead of calculating or answering based on stored data.
errors: No technical errors, just lack of contextual information in the prompt.
reproduction: 1. Log in as a user with profile data. 2. Ask the chatbot: "How much should I eat to be in a surplus?" or "Is my current weight healthy for my height?" 3. AI asks for weight/height instead of calculating or answering based on stored data.
started: Feature gap identified during user testing.

## Eliminated

## Evidence

- timestamp: 2025-05-15T10:05:00Z
  checked: backend/app/routers/chat.py
  found: _build_context_prompt only includes tdee_kcal and goal. tdee_kcal is fetched from profile dict but not present in users table (verified in app/database.py).
  implication: The chatbot context is indeed missing the requested profile fields. Also, TDEE might be "unknown" if it's not pre-calculated and added to the profile dict before calling _build_context_prompt.

- timestamp: 2025-05-15T10:10:00Z
  checked: backend/app/database.py
  found: users table contains weight_kg, height_cm, age, gender, activity_level, goal. It does NOT contain tdee_kcal.
  implication: We need to pull these fields from the DB and pass them to the prompt builder.

- timestamp: 2025-05-15T10:15:00Z
  checked: backend/app/utils/nutrition.py
  found: Contains calculate_bmr, calculate_tdee, and adjust_for_goal.
  implication: We can use these to provide an accurate TDEE/target in the context if needed, though providing raw data is also required.


## Resolution

root_cause: The _build_context_prompt function in app/routers/chat.py was only including goal and a (missing) tdee_kcal field, ignoring the detailed profile data (weight, height, age, gender, activity_level) available in the users table.
fix: Update _build_context_prompt to include all relevant user metrics and calculate TDEE on the fly using existing utilities.
verification: Manual verification through chatbot interaction (simulated or unit test).
files_changed: [backend/app/routers/chat.py]
