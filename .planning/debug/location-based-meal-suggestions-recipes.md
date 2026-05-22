---
status: resolved
trigger: "Investigate issue: location-based-meal-suggestions-recipes"
created: "2026-05-20T12:00:00Z"
updated: "2026-05-20T12:00:00Z"
---

## Current Focus

hypothesis: The frontend is not fetching location-based meal suggestions from the backend, and the click handler for suggestions is not implemented.
test: Examine the frontend code for meal suggestions and related API calls.
expecting: To find the component responsible for displaying meal suggestions and identify the missing logic for location-awareness and click handling.
next_action: Search the codebase for "suggestion" to find relevant files.

## Symptoms

expected: Based on user data, Gemma 4 should generate location-aware meal suggestions; clicking a suggested meal in the UI should show a recipe, required items, and nutritional values.
actual: Meal suggestions are not based on the user's location and clicking suggested meals does nothing.
errors: None reported.
reproduction: Not specified.
started: Not specified.

## Eliminated

-

## Evidence

- 2026-05-20T12:05:00Z: `grep_search` for "suggestion" pointed to `backend/app/routers/planning.py` and frontend components.
- 2026-05-20T12:10:00Z: Reading `backend/app/routers/planning.py` revealed that the `/suggest` endpoint uses the user's location from the `current_user` object.
- 2026-05-20T12:15:00Z: Reading `frontend/src/context/AuthContext.jsx` showed that the user's location was not being fetched or sent to the backend.
- 2026-05-20T12:25:00Z: `file_search` for `MealPlanner` located `frontend/src/components/planner/MealPlanner.jsx`.
- 2026-05-20T12:30:00Z: Reading `MealPlanner.jsx` showed it was using a local, non-API-based suggestion engine and had no click handlers on recipe cards.

## Resolution

root_cause: The frontend was using a hardcoded, local recipe suggestion engine and did not fetch the user's location. The UI was not configured to handle clicks on meal suggestions.
fix: 
1.  Modified `frontend/src/context/AuthContext.jsx` to get the user's geolocation and update the user profile on the backend.
2.  Modified `frontend/src/components/planner/MealPlanner.jsx` to fetch meal suggestions from the `/api/planning/suggest` endpoint.
3.  Created `frontend/src/components/planner/RecipeModal.jsx` to display recipe details.
4.  Updated `frontend/src/components/planner/MealPlanner.jsx` to open the modal when a recipe is clicked.
verification: The meal suggestions are now location-aware, and clicking on a suggestion opens a modal with the recipe details.
files_changed: 
- `c:\Users\OM Prakash\Documents\NutriSnap\frontend\src\context\AuthContext.jsx`
- `c:\Users\OM Prakash\Documents\NutriSnap\frontend\src\components\planner\MealPlanner.jsx`
- `c:\Users\OM Prakash\Documents\NutriSnap\frontend\src\components\planner\RecipeModal.jsx`
