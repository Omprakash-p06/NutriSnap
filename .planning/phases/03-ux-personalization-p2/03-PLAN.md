# Phase 3 Plan: UX & Personalization (P2)

## Objective
Finalize the user experience with an offline-first progress dashboard and a rule-based meal planner. This phase transitions NutriSnap from a scanning tool to a comprehensive nutrition companion by providing actionable insights even without connectivity.

## Tech Stack
- **Dashboard:** Recharts (Data Viz)
- **Offline Storage:** Dexie.js (IndexedDB wrapper with multi-user support via `userId`)
- **Logic:** date-fns (Dates), fitness-calc (Metabolic math)
- **PWA:** vite-plugin-pwa (Service Workers & Offline manifests)

## Wave Structure

| Wave | Plan | Objective | Autonomous |
|------|------|-----------|------------|
| 1 | [03-01](./03-01-PLAN.md) | Meal Planner Engine (Logic & Schema) | Yes |
| 1 | [03-02](./03-02-PLAN.md) | Offline Aggregation & Dexie Setup (with userId) | Yes |
| 2 | [03-03](./03-03-PLAN.md) | Progress Dashboard & Visualizations | Yes |
| 3 | [03-04](./03-04-PLAN.md) | PWA Polish & E2E Integration | Yes |

## Must-Haves (Goal-Backward)

### Observable Truths
1. User sees 3 personalized meal suggestions based on their remaining calorie/macro budget.
2. User views a 7-day bar chart showing calorie intake vs. target.
3. User can continue logging meals and viewing history while offline, with data scoped to their account.
4. App prompts the user to refresh when a new version is available.

### Critical Artifacts
- `src/services/planner/engine.js`: Pure functions for meal matching.
- `src/services/db.js`: Dexie configuration for offline storage (scoped by `userId`).
- `src/services/aggregator.js`: Logic to bucket meals by day for charting.
- `src/components/dashboard/ProgressDashboard.jsx`: Visualization layer using Recharts.

## Verification
- **Automated**: unit tests for the recommendation engine (`npm test`) and Dexie schema validation via content checks in CI.
- **Manual**: Toggle "Offline" in DevTools, log a meal, and verify it persists in the "History" tab after refresh.
- **Visual**: Verify Recharts `BarChart` and `PieChart` responsiveness on mobile breakpoints (375px width).

## Success Criteria
- [ ] Meal planner suggests high-protein options when protein is the largest gap.
- [ ] Dexie schema includes `userId` for data isolation.
- [ ] Weekly summary correctly calculates 7 days of historical totals.
- [ ] PWA installation prompt appears on supported browsers.
