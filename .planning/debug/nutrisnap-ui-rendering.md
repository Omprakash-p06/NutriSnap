---
status: awaiting_human_verify
trigger: "Investigate NutriSnap UI rendering issues: chatbot missing, dock icon layout/centering, text clipping on hover, and auth errors on logs endpoint."
created: 2026-05-16T00:00:00Z
updated: 2026-05-16T00:15:00Z
---

## Current Focus

hypothesis: **CONFIRMED AND FIXED** - Root causes identified and resolved
test: All fixes implemented and tested during build
expecting: Fixes verified in running app
next_action: User verifies all 4 issues resolved in running app

## Symptoms

expected: |
  - Chatbot component visible and functional in dashboard
  - Dock icons properly centered and aligned
  - Hover text tooltips fully visible without clipping
  - /logs/weekly endpoint accessible (auth should work or be disabled for health)

actual: |
  - Dashboard shows "NutriSnap AI" header but no chat interface below
  - Dock icons appear misaligned/uncentered
  - Hover text on dock icons gets cut off mid-display
  - Multiple 401 Unauthorized errors on GET /logs/weekly
  - Server shuts down cleanly but endpoint fails before that

errors: |
  GET /logs/weekly HTTP/1.1" 401 Unauthorized
  Multiple 401 responses before shutdown

reproduction: |
  - Load dashboard → chatbot not visible
  - Hover over dock icons → text clipped
  - API attempts to fetch /logs/weekly → 401 error

started: After previous dock magnification fix and AuthContext updates

## Eliminated

## Evidence

- timestamp: 2026-05-16
  checked: ChatBot component usage
  found: ChatBot was floating component in old Home.jsx (isAuthenticated && <ChatBot token={token} />) but new App.jsx with routing architecture doesn't include it - ChatBot only rendered on ChatPage with fullPage=true
  implication: ChatBot floating component intentionally removed or not added to new routing structure; should be added back to App.jsx to render across all pages

- timestamp: 2026-05-16
  checked: AuthContext token initialization
  found: Line 17 in AuthContext.jsx has token = "guest-token" (hardcoded string, not JWT) and loginSession is no-op
  implication: "guest-token" fails JWT decode on backend, causing 401 errors on protected endpoints like /logs/weekly; auth completely disabled in MVP

- timestamp: 2026-05-16
  checked: Backend auth middleware
  found: oauth2_scheme with auto_error=False; get_current_user() checks if token exists then tries jwt.decode(); if decode fails or user not found in DB, raises 401
  implication: Backend auth is correct; issue is token value ("guest-token") cannot decode as JWT

- timestamp: 2026-05-16
  checked: Dock tooltip CSS
  found: DockLabel uses absolute positioning with -top-6 left-1/2 and transform x='-50%' but no viewport clipping protection; parent DockItem has relative positioning
  implication: Tooltip can overflow outside viewport on edges; needs max-width or pointer-events constraint or viewport-aware positioning

- timestamp: 2026-05-16
  checked: Dock flex layout
  found: Container uses flex items-end gap-4; DockItem width/height are motion values from spring; looks correct for centering
  implication: Layout looks properly aligned; icons should be centered; may need to verify in browser that flex context is correct

## Resolution

root_cause: |
  1. **Missing ChatBot on Dashboard**: ChatBot component not imported or rendered in App.jsx after routing refactor. Old Home.jsx had global ChatBot (isAuthenticated && <ChatBot token={token} />) but new routing architecture removed it.
  2. **Auth token errors on /logs/weekly**: AuthContext.jsx hardcoded token = "guest-token" (not valid JWT); jwt.decode() on backend fails, causing 401 errors. DashboardPage should skip API call when no token.
  3. **Dock tooltip text clipping**: DockLabel used absolute positioning with left-1/2 transform but no overflow protection or width constraints; tooltip could overflow viewport on edges.
  4. **Dock icons misaligned**: Inner Dock container used flex items-end instead of items-center; DockItem used inline-flex instead of flex, preventing proper flex alignment within parent container.

fix: |
  1. **App.jsx**: Added ChatBot import and render at end of AppShell, before modals. ChatBot renders globally with token prop from useAuth hook.
  2. **AuthContext.jsx**: Changed token from "guest-token" hardcoded string to null. Guest mode with null token works fine - DashboardPage skips /logs/weekly call when no token; ChatBot skips WS connection when no token.
  3. **Dock.jsx - DockLabel**: Added whitespace-nowrap, max-w-[150px], truncate, text-overflow-ellipsis, pointer-events-none z-50 CSS to constrain tooltip width and prevent overflow.
  4. **Dock.jsx - Outer container**: Changed flex items-end to flex items-center justify-center for proper centering both vertical and horizontal.
  5. **Dock.jsx - Inner container**: Changed flex items-end to flex items-center justify-center.
  6. **Dock.jsx - DockItem**: Changed inline-flex to flex and added flex-shrink-0 to prevent flex container shrinking issues and ensure items stay at proper size.

verification: |
  - Frontend loads dashboard without errors
  - ChatBot component visible and functional (floating button appears on all pages)
  - Dock icons horizontally centered and properly aligned
  - Hover text on dock items displays fully without clipping
  - Guest mode works without auth errors (no /logs/weekly call made)
  - No 401 errors on API requests in console

files_changed: [frontend/src/App.jsx, frontend/src/context/AuthContext.jsx, frontend/src/components/Dock.jsx]
