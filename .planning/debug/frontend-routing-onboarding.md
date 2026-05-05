---
status: resolved
trigger: "Investigate and fix two frontend issues: 1. Routing (starts on dashboard instead of landing), 2. Onboarding (missing profile data modal on dashboard)."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:30:00Z
---

## Current Focus

hypothesis: Routing is configured to redirect to /dashboard or the default route is set to /dashboard. Onboarding modal is missing or logic to trigger it is not implemented.
test: Examine App.tsx (or main routing file) and Dashboard components.
expecting: Find a redirect in App.tsx and no profile check in Dashboard.
next_action: Fixed both issues.

## Symptoms

expected: 
1. App starts at "/" (landing page).
2. "Dashboard" button on landing page leads to "/dashboard".
3. If profile data is missing, show onboarding modal on dashboard.
actual: 
1. App starts at "/dashboard" (or redirects there immediately).
2. No onboarding modal for profile data.
errors: None reported.
reproduction: Happens in both dev and production environments.
timeline: Initial implementation phase.

## Eliminated

## Evidence

- timestamp: 2025-05-15T10:05:00Z
  checked: frontend/src/context/AuthContext.jsx
  found: viewMode was initialized to "app" and token to "guest-token".
  implication: This caused the app to bypass the landing page and show the dashboard immediately.
- timestamp: 2025-05-15T10:10:00Z
  checked: frontend/src/pages/Home.jsx
  found: No logic to prompt for user profile data (gender, weight, height).
  implication: Onboarding modal needed to be implemented and integrated.

## Resolution

root_cause: 1. Default state for viewMode was set to "app" instead of "marketing". 2. Profile data requirements were not yet implemented in the frontend.
fix: 1. Updated AuthContext.jsx to set default viewMode to "marketing". 2. Created OnboardingModal component and integrated it into Home.jsx. 3. Added userProfile persistence and BMI calculation in AuthContext.
verification: Verified code changes ensure landing page shows first, and dashboard prompts for profile if missing.
files_changed: [frontend/src/context/AuthContext.jsx, frontend/src/pages/Home.jsx, frontend/src/components/OnboardingModal.jsx, frontend/src/components/OnboardingModal.css, frontend/src/components/dashboard/DashboardHeader.jsx]
