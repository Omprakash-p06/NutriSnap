---
status: diagnosed
trigger: "Scanning an image clears the entire dashboard UI (meals, insights, hydration). When user returns to dashboard, suggested meals regenerate (breaking rate limit efficiency)."
created: 2026-05-07T00:00:00Z
updated: 2026-05-07T00:30:00Z
---

## Current Focus

hypothesis: CONFIRMED - Conditional rendering in Home.jsx unmounts entire dashboard (DashboardPage → MealPlanner). When remounting, MealPlanner's useEffect runs on mount (before dependency check), calling fetchSuggestions() again.

test: Examined Home.jsx AnimatePresence, DashboardPage, and MealPlanner.jsx dependencies. Traced the mount/unmount → re-fetch cycle.

expecting: Verified the exact mechanism causing the re-fetch. Ready to plan fix.

next_action: Plan the fix. Two approaches identified: (1) keep dashboard mounted (hide instead of unmount), or (2) add caching to prevent re-fetch on remount.

## Symptoms

expected: Dashboard remains visible while scanning. After returning from scan results, meals DO NOT regenerate unless user clicks "Refresh Suggestions" button.

actual:
1. Click scan/upload image → dashboard disappears (MealList, DashboardPage, MealPlanner all gone)
2. Scan completes, click "back" or close results → dashboard reappears
3. Reappeared dashboard regenerates suggested meals (instead of using cached suggestions)
4. This forces re-fetching from API even if user didn't click refresh

reproduction:
1. Load app, see dashboard with meal suggestions
2. Click Camera/Upload → start scan/search
3. Observe all dashboard UI vanishes
4. Complete scan → results display
5. Click "back" or close results
6. Observe dashboard reappears WITH NEW meal suggestions (different cards than before)

## Eliminated

## Evidence

- timestamp: 2026-05-07T00:00:00Z
  checked: Provided context
  found: User identified Home.jsx lines 176-217 as the conditional rendering location
  implication: Know where to look first

- timestamp: 2026-05-07T00:10:00Z
  checked: Home.jsx lines 176-217
  found: |
    ```jsx
    {!result && !image && !isAnalyzing && (
      <motion.div>
        <section>
          <InsightCards />
          <MealList />
          <HydrationWidget />
          <DashboardPage />
        </section>
      </motion.div>
    )}
    ```
  implication: ENTIRE dashboard section unmounts when result becomes truthy. This includes DashboardPage and all its children (MealPlanner).

- timestamp: 2026-05-07T00:15:00Z
  checked: MealPlanner.jsx
  found: |
    useEffect(() => {
      fetchSuggestions();
    }, [currentIntake?.meals_logged, targets?.target_calories]);
  implication: useEffect runs on mount. Even if dependencies match, the effect ALWAYS runs on component mount. This is standard React behavior.

- timestamp: 2026-05-07T00:20:00Z
  checked: MealPlanner state management
  found: useState([]) for suggestions means all state is lost on unmount
  implication: When DashboardPage unmounts → MealPlanner unmounts → suggestions state is discarded. When remounting, useState re-initializes to [].

- timestamp: 2026-05-07T00:25:00Z
  checked: User flow
  found: |
    1. Dashboard renders with suggestions from useEffect
    2. User clicks scan → result = data → {!result && ...} = false → UNMOUNT
    3. User sees results
    4. User goes back → result = null → {!result && ...} = true → REMOUNT
    5. MealPlanner mounts → useEffect runs → fetchSuggestions called
    6. API response replaces lost suggestions
  implication: The combination of unmount + useEffect-on-mount guarantees a re-fetch even with unchanged dependencies.

## Resolution

## Resolution

root_cause: |
  Conditional rendering in Home.jsx (lines 176-217) uses AnimatePresence with condition {!result && !image && !isAnalyzing}. This UNMOUNTS the entire dashboard section (DashboardPage, MealPlanner, and all meal suggestions) when result is set.
  
  When user returns from scan and result is cleared, the dashboard REMOUNTS. Upon remount:
  - MealPlanner component mounts (React lifecycle)
  - useEffect runs automatically on mount (standard React behavior)
  - fetchSuggestions() is called, triggering API request
  - Suggestions are fetched again even though they're unchanged
  
  Root cause: Unmounting state-based components loses cached suggestions. Remounting triggers useEffect which fetches new data, breaking rate-limit efficiency.

fix: |
  APPROACH 1 (Recommended): Keep dashboard mounted, hide with CSS/opacity instead of unmount
  - Wrap dashboard in <div style={{ display: result ? 'none' : 'block' }}>
  - Prevents component unmount → preserves state and prevents useEffect re-run
  - useEffect only runs once when component mounts (on app load), never again
  
  APPROACH 2 (Alternative): Add caching at API level or in Home.jsx context
  - Cache suggestions in Home.jsx state
  - Pass cached suggestions to DashboardPage → MealPlanner
  - Only re-fetch if user clicks "Refresh" button (explicit action)
  - Prevents accidental re-fetches from remounting

verification: [pending - user to test after implementation]

files_changed: []
