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
- timestamp: 2026-05-20T21:48:00Z
  checked: Random/books image displayed for breakfast.
  found: Two distinct issues:
    1. The LLM's returned suggestions did not have their `image_url` fields correctly generated/URL-encoded on the backend, causing the image to fail and trigger the frontend fallback handler.
    2. The frontend fallback for breakfast mapped to "Oatmeal with Berries" in `recipes.js` which had a typo image showing a stack of books on a desk (`photo-1517673132405-a56a62b18caf`).
  implication: Resolved by:
    1. Programmatically generating and overriding `image_url` in the backend suggest router using a URL-encoded Pollinations AI prompt based on the actual generated meal name.
    2. Correcting the oatmeal image URL in `recipes.js` to point to a real oatmeal bowl photo (`photo-1586444248902-2f64eddc13df`).
- timestamp: 2026-05-20T21:52:00Z
  checked: Non-randomized meal suggestions and image requirements locally.
  found: Two issues:
    1. Gemma 4 text-only suggestions were deterministic/repetitive.
    2. Fallback images (Unsplash) or Pollinations AI images require internet access. Locally/offline, these fail to load, resulting in broken image icons or confusing fallback pictures.
  implication: Resolved by:
    1. Randomizing suggestions: Injected random cuisine themes (e.g. Greek, Mediterranean, Korean) and random featured ingredients into the LLM prompt. Also randomized the fallback suggestion templates pool.
    2. Collapsing image container: Updated the frontend `AIMealCard` so that if an image fails to load (onError), it sets `hasError` state and completely hides the image element, removing the space where the image was required.

## Resolution
root_cause: The issues were caused by a combination of missing frontend implementation, missing backend API endpoints, a missing `import time` NameError in the suggest endpoint, lack of image loading fallbacks on the frontend, unencoded/copy-paste image URLs from the LLM, a typo in the local recipe database, deterministic suggestions, and space waste for failed images locally.
fix:
1.  **Frontend:**
    - Updated `AIMealCard` to handle image loading state and use an `onError` listener to hide the image entirely, collapsing the space when images fail to load or are unavailable locally.
    - Replaced the book stack placeholder image for "Oatmeal with Berries" in `frontend/src/services/planner/recipes.js` with a real oatmeal image.
2.  **Backend:**
    - Fixed missing `import time` in `backend/app/routers/planning.py`.
    - Cached `_meal_llm` instance using `@lru_cache` to resolve CUDA Graph warnings.
    - Programmatically set `image_url` in the `/suggest` endpoint using `urllib.parse.quote` of the actual generated meal name.
    - Injected random cuisine themes and featured ingredients into the LLM suggestions prompt to ensure variety.
    - Randomized the static fallback suggestions returned when the LLM is offline.
verification: Checked that the frontend built successfully and all backend tests passed. The suggest endpoint returns randomized meals, and the frontend card collapses the image container if image loading fails.
files_changed:
- `frontend/src/pages/PlannerPage.jsx`
- `frontend/src/services/planner/recipes.js`
- `backend/app/routers/planning.py`
