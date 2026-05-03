# Phase 3 Research: UX & Personalization (P2)

## Standard Stack
- **Dashboard:** [Recharts](https://recharts.org/) (already used in `nutrisnap-new`).
- **Data Aggregation:** [Dexie.js](https://dexie.org/) for offline-first IndexedDB management.
- **Date Logic:** [date-fns](https://date-fns.org/) for multi-day grouping and range logic.
- **Metabolic Math:** [@finegym/fitness-calc](https://www.npmjs.com/package/@finegym/fitness-calc) for BMR, TDEE, and macro targets.
- **PWA Polish:** [vite-plugin-pwa](https://vite-pwa-org.netlify.app/) with Workbox Background Sync.

## Architecture Patterns
- **Rule-based Planner:** **Filtering Pipeline Pattern**.
  - A sequence of pure functions: `filter(recipes, constraints) -> score(results, preferences) -> select(best)`.
  - Suggestions should be computed locally to maintain "Easy & Hassle-Free" offline core value.
- **Dashboard Data Flow:** **Offline-First Aggregation**.
  - UI binds to Dexie live queries.
  - Background processes calculate multi-day totals into a "Chart View" cache table.

## Don't Hand-Roll
- **Metabolic Formulas:** Mifflin-St Jeor or Harris-Benedict formulas are prone to manual math errors. Use `fitness-calc`.
- **Date Grouping:** Hand-rolling "group by day/week" with JS `Date` is complex due to timezones and leap years. Use `date-fns`.
- **IndexedDB Boilerplate:** Raw IndexedDB is extremely verbose. Use `Dexie.js`.

## Common Pitfalls
- **Workbox Sync Failures:** Background sync can fail on iOS if the app is killed. Ensure there's a manual "Retry Sync" UI.
- **Recharts Performance:** Rendering 30+ days of data on mobile can lag. Use `isAnimationActive={false}` for large datasets.
- **PWA Update UX:** Users often miss service worker updates. Implement a "New update available - Refresh" toast.

## Code Examples
### Rule Pipeline Example
```javascript
const suggestMeal = (recipes, goals) => {
  return recipes
    .filter(r => r.calories < goals.remainingCalories)
    .sort((a, b) => scoreMacroBalance(b, goals) - scoreMacroBalance(a, goals))
    .slice(0, 3);
};
```
