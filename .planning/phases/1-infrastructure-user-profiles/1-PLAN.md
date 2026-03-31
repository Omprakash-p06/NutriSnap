---
wave: 1
depends_on: []
files_modified:
  - backend/models/user.py
  - backend/schemas/user.py
  - backend/routes/user.py
  - backend/main.py
  - frontend/src/pages/Profile.tsx
autonomous: true
requirements_addressed: [USR-01, USR-02, USR-03]
---

# Phase 1: Infrastructure - User Profiles

## Goal
Establish health profiles and daily macro targets.

## Must Haves
1. User can persist BMI and Goals in the datastore.
2. The User model cleanly calculates internal daily baseline macros.

## Implementation Steps

<task>
<objective>Extend DB schema and schemas for User BMI and Macros</objective>
<read_first>
- backend/models/user.py
- backend/schemas/food.py (For reference)
</read_first>
<action>
Modify `backend/models/user.py`:
- Import `Float` alongside existing imports.
- Add fields: `bmi = Column(Float, nullable=True)`
- Add fields: `daily_target_protein_g = Column(Float, default=150.0)`, `daily_target_carbs_g = Column(Float, default=200.0)`, `daily_target_fats_g = Column(Float, default=65.0)`.

Create `backend/schemas/user.py`:
- Add Pydantic `UserProfileBase` with fields: `name`, `height_cm`, `weight_kg`, `age`, `activity_level`, `goal`. (All Optional to aid patching).
- Add Pydantic `UserProfileUpdate` identical to base.
- Add Pydantic `UserProfileResponse` with base fields AND `bmi`, `daily_target_kcal`, `daily_target_protein_g`, `daily_target_carbs_g`, `daily_target_fats_g`, `id`.
</action>
<acceptance_criteria>
- `backend/models/user.py` contains `bmi = Column(Float`
- `backend/models/user.py` contains `daily_target_protein_g = Column(Float`
- `backend/schemas/user.py` contains `class UserProfileResponse`
</acceptance_criteria>
</task>

<task>
<objective>Create User Profile API Router</objective>
<read_first>
- backend/routes/user.py
- backend/main.py
- backend/schemas/user.py
</read_first>
<action>
Create `backend/routes/user.py`:
- Implement `GET /api/v1/user/profile` returning the first user from the DB (or creating a default Guest user if none exist).
- Implement `PUT /api/v1/user/profile` that accepts `UserProfileUpdate`.
- In PUT, calculate `bmi` (weight_kg / (height_cm/100)^2).
- In PUT, calculate TDEE base calories using standard math from the payload's age/height/weight and activity_level (sedentary=1.2, moderate=1.55, active=1.725). Add/subtract deficit depending on goal ("lose"=-500, "gain"=+300).
- Distribute TDEE into Macros: 30% Protein (4 kcal/g), 40% Carbs (4 kcal/g), 30% Fats (9 kcal/g). Calculate the exact gram amounts and store them in the `daily_target_*` fields along with the `daily_target_kcal`.
- Commit changes to the DB session and return the updated user as `UserProfileResponse`.

Modify `backend/main.py`:
- Import `router as user_router` from `backend.routes.user`.
- Call `app.include_router(user_router, prefix="/api/v1/user", tags=["user"])`. Notice the prefix adjustment to match the frontend expectations.
</action>
<acceptance_criteria>
- `backend/routes/user.py` contains `@router.put("/profile"`
- `backend/routes/user.py` contains the math string `0.30` or `30` indicating macro split calculation
- `backend/main.py` contains `app.include_router(user_router`
</acceptance_criteria>
</task>

<task>
<objective>Connect Frontend UI to new User Backend</objective>
<read_first>
- frontend/src/pages/Profile.tsx
</read_first>
<action>
Modify `frontend/src/pages/Profile.tsx`:
- Add `useEffect` to trigger a cross-fetch (`GET /api/v1/user/profile`). Set the form state from the response.
- In `handleSave()`, send a `PUT /api/v1/user/profile` with the populated profile JSON payload, and update the state using the server's response.
- Completely remove the UI-side localized TDEE calculation inside `handleSave()`, relying exclusively on the backend's response payload.
- In the `Daily Target` render section (bottom of component), additionally display the exact split values (Protein: {profile.daily_target_protein_g}g, Carbs: {profile.daily_target_carbs_g}g, Fats: {profile.daily_target_fats_g}g) to properly reflect the new macros added in DB.
</action>
<acceptance_criteria>
- `frontend/src/pages/Profile.tsx` contains `fetch('/api/v1/user/profile'`
- `frontend/src/pages/Profile.tsx` does NOT contain `const bmr = 10 * weight`
</acceptance_criteria>
</task>
