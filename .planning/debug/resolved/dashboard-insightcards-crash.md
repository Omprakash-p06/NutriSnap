---
status: investigating
trigger: "Investigate and fix the 'Something went wrong' error occurring on the dashboard."
created: 2025-05-15T10:00:00Z
updated: 2025-05-15T10:10:00Z
---

## Current Focus

hypothesis: The 'currentIndex' state can become out of bounds if the 'insights' array is updated with a shorter array, leading to 'current' being undefined.
test: Add defensive checks for 'current' and ensure 'currentIndex' is reset or clamped when 'insights' change.
expecting: A fix to prevent 'current.type' access on undefined.
next_action: Verify if 'insights' can change length during session and implement fix.

## Symptoms

expected: Dashboard should load and display insights/history without crashing.
actual: "Something went wrong" message appears. Insights and logs are not visible.
errors: 
- Uncaught SyntaxError: expected expression, got '<' registerSW.js:1:1
- TypeError: can't access property "type", current is undefined in InsightCards.jsx:70
reproduction: Open the dashboard and view the Insights section.
started: Started after font unification across the UI.

## Eliminated

## Evidence

- timestamp: 2025-05-15T10:05:00Z
  checked: InsightCards.jsx
  found: The component accesses 'current.type' (line 66, 70, 89, 107) where 'current = insights[currentIndex]'.
  implication: If 'currentIndex >= insights.length', 'current' is undefined. This can happen if 'insights' is updated to a shorter array while 'currentIndex' is high.

## Resolution

root_cause: The 'InsightCards' component was not defensively handling cases where 'insights' might not be an array (e.g., when the API returns an error object) or when 'currentIndex' becomes out of bounds. This caused 'current' to be undefined, leading to a crash when accessing 'current.type'.
fix: Added defensive checks in InsightCards.jsx to ensure 'insights' is an array, 'currentIndex' is safe, and 'current' is defined before rendering.
verification: Added 'safeIndex' and 'current' check.
files_changed: [frontend/src/components/dashboard/InsightCards.jsx]
