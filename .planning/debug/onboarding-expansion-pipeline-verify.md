---
status: investigating
trigger: "Enhance the NutriSnap frontend and backend while verifying the scanning pipeline. 1. UI Cleanup: Remove the 'snap circle' feature from the dashboard. 2. Onboarding Expansion: Update onboarding flow, ensure data persistence. 3. Health Calculations: Implement TDEE, Protein, Water intake. 4. AI Flexibility: Support multiple AI providers. 5. Pipeline Verification: Test scanning pipeline."
created: 2025-05-15T12:00:00Z
updated: 2025-05-15T12:00:00Z
---

## Current Focus

hypothesis: Initial exploration to locate target components and logic.
test: Search for "snap circle", onboarding flow, health calculations, and AI validation logic.
expecting: Identify files to modify.
next_action: Search for "snap circle" in frontend.

## Symptoms

expected: 
1. No snap circle on dashboard.
2. Onboarding modal collects age, sex, activity, goals, preferences.
3. Calculations (TDEE, protein, water) are accurate and reflected in suggestions.
4. Scanning pipeline works and can be validated with multiple AI providers.
actual:
1. Snap circle exists.
2. Onboarding only collects height/weight/gender.
3. Calculations are basic BMI only.
4. Validation is Gemini-specific.
reproduction: Development and production.
started: Post-initial onboarding implementation.

## Eliminated

## Evidence

## Resolution

root_cause: 
fix: 
verification: 
files_changed: []
