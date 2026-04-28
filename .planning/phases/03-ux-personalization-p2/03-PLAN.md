# Phase 3 Plan: UX & Personalization (P2)

## Objective
Finalize the user experience with an offline-first progress dashboard and a rule-based meal planner. This phase transitions NutriSnap from a scanning tool to a comprehensive nutrition companion.

## Tech Stack
- **Dashboard:** Recharts (Data Viz)
- **Offline Storage:** Dexie.js (IndexedDB wrapper)
- **Logic:** date-fns (Dates), fitness-calc (Metabolic math)
- **PWA:** vite-plugin-pwa (Service Workers)

## Wave Structure

| Wave | Plan | Objective | Autonomous |
|------|------|-----------|------------|
| 1 | [03-01](./03-01-PLAN.md) | Meal Planner Engine (Logic & Schema) | Yes |
| 1 | [03-02](./03-02-PLAN.md) | Offline Aggregation & Dexie Setup | Yes |
| 2 | [03-03](./03-03-PLAN.md) | Progress Dashboard & Visualizations | Yes |
| 3 | [03-04](./03-04-PLAN.md) | PWA Polish & E2E Integration | Yes |

## Must-Haves (Goal-Backward)

### Observable Truths
1. User sees 3 personalized meal suggestions based on their remaining calorie/macro budget.
2. User views a 7-day bar chart showing calorie intake vs. target.
3. User can continue logging meals and viewing history while offline.
4. App prompts the user to refresh when a new version is available.

### Critical Artifacts
- `src/services/planner/engine.js`: Pure functions for meal matching.
- `src/services/db.js`: Dexie configuration for offline storage.
- `src/services/aggregator.js`: Logic to bucket meals by day for charting.
- `src/components/dashboard/ProgressDashboard.jsx`: Visualization layer.

## Verification
- **Automated**: Dexie schema validation and unit tests for the recommendation engine.
- **Manual**: Toggle "Offline" in DevTools and verify meal logging still works.
- **Visual**: Confirm Recharts responsiveness on mobile breakpoints.
