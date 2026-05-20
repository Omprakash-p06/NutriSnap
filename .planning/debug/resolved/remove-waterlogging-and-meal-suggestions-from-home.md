---
status: resolved
trigger: "Remove water logging and suggested meals from home page, show daily progress with a good graph"
created: 2026-05-20T22:11:00Z
updated: 2026-05-20T22:15:00+05:30
---

## Current Focus
hypothesis: The user wants to remove HydrationWidget (water logging) and MealPlanner (suggested meals) from the main home page (Dashboard tab) because they are already present on dedicated pages. They want the dashboard to focus purely on daily progress and trends using interactive, beautiful graphs.
expecting: The Dashboard page should display today's progress ring card, macro breakdown pie chart, and a comprehensive weekly trends graph that toggles between calories and macros. HydrationWidget and MealPlanner should be completely removed from the dashboard page.

## Resolution
root_cause: The dashboard page (`DashboardPage.jsx`) rendered several redundant widgets (hydration widget and AI meal planner) alongside progress widgets.
fix:
1.  **Backend (`backend/app/routers/logs.py`):**
    - Updated `/logs/weekly` to select and sum `protein`, `carbs`, and `fat` as well as `calories` for each day, ensuring the trend data contains complete information.
2.  **Frontend:**
    - Modified `ProgressDashboard.jsx` to be interactive: added a tab control that allows toggling between Calories and Macronutrients. When on Calories, it displays a BarChart with a reference target line. When on Macronutrients, it displays a premium stacked AreaChart with emerald/teal gradients. Explicitly defined heights on Recharts containers to prevent height warnings.
    - Modified `DashboardPage.jsx` to remove `HydrationWidget` and `MealPlanner`.
    - Added a modern today's calories progress card inside `DashboardPage.jsx` featuring the `ProgressRing` component alongside remaining calories and completion percentages.
verification: Checked that the frontend built successfully and all backend tests passed.
files_changed:
- `backend/app/routers/logs.py`
- `frontend/src/components/dashboard/ProgressDashboard.jsx`
- `frontend/src/pages/DashboardPage.jsx`
