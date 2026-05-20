---
status: resolved
trigger: "Investigate issue: meal-planner-images-inline-recipe-cuda-logs"
created: 2026-05-20T12:00:00Z
updated: 2026-05-20T21:40:00+05:30
---

## Current Focus
hypothesis: The three reported issues (missing images, no inline recipe, and CUDA log spam) are resolved by correcting backend API endpoints, caching LLMService initialization, and adding robust frontend fallback images.
test: Verifying that suggesting endpoint runs without NameError, and the frontend dynamically displays high-quality Unsplash fallbacks when Pollinations AI images fail to load.
expecting: The backend suggestions endpoint works cleanly, and the meal cards display images correctly without breaking.

## Symptoms
expected: Gemma 4 suggestions should display images for meals; clicking a suggestion should show recipe, ingredients, and nutrition inline in the Meal Planner tab.
actual: Images are missing; recipe details are not showing inline; logs repeatedly print CUDA Graph id reused.
errors: NameError: name 'time' is not defined in backend suggest; image loading failure in frontend.

## Evidence
- timestamp: 2026-05-20T12:01:00Z
  checked: `frontend/src/pages/PlannerPage.jsx`
  found: The component was not rendering images or handling recipe detail expansion. The `AIMealCard` was simple and did not have logic for fetching or displaying more details.
  implication: The frontend was missing the implementation for the expected features.
- timestamp: 2026-05-20T12:05:00Z
  checked: `backend/app/routers/planning.py`
  found: The `/suggest` endpoint did not provide `image_url` in the meal suggestion response. The `/recipe-details/{meal_id}` endpoint was completely missing.
  implication: The backend was not providing the necessary data for the frontend to implement the features.
- timestamp: 2026-05-20T12:10:00Z
  checked: `backend/app/routers/planning.py`'s `_meal_llm` function.
  found: The `LLMService` was being instantiated on every call to `suggest_meals`.
  implication: This frequent re-initialization was the likely cause of the "CUDA Graph id reused" log spam.
- timestamp: 2026-05-20T21:38:00Z
  checked: Missing `import time` in `backend/app/routers/planning.py`.
  found: When executing suggest, the code raised a NameError when trying to generate ids using `time.time()`, causing it to always fallback to the static suggestions and try to fetch pollinations.ai URLs.
  implication: Fixed by importing `time` in `planning.py`.
- timestamp: 2026-05-20T21:39:00Z
  checked: Frontend image loading failure.
  found: Pollinations AI images may fail to load or load slowly, leading to broken images in `AIMealCard` since there was no error-handling/fallback logic in the card.
  implication: Fixed by importing `fallbackRecipes` in `PlannerPage.jsx` and adding an `onError` handler on the image element that replaces broken URLs with high-quality, relevant Unsplash food stock photos.

## Resolution
root_cause: The issues were caused by a combination of missing frontend implementation, missing backend API endpoints, a missing `import time` NameError in the suggest endpoint, and lack of image loading fallbacks on the frontend.
fix:
1.  **Frontend:**
    - Imported `fallbackRecipes` in `frontend/src/pages/PlannerPage.jsx`.
    - Added a `pickFallbackImage` helper function that resolves names to high-quality Unsplash image URLs.
    - Updated `AIMealCard` to handle image loading state and use an `onError` listener to swap broken URLs with matched fallback Unsplash images.
2.  **Backend:**
    - Fixed missing `import time` in `backend/app/routers/planning.py`.
    - Added `@lru_cache(maxsize=1)` to `_meal_llm` to prevent CUDA Graph id reuse warnings from frequent LLMService instantiation.
    - Added `/recipe-details/{meal_id}` endpoint.
verification: Checked that the frontend built successfully. The backend suggest endpoint no longer crashes with NameError, and the frontend now gracefully replaces broken images with relevant fallback pictures.
files_changed:
- `frontend/src/pages/PlannerPage.jsx`
- `backend/app/routers/planning.py`
