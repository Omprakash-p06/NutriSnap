---
status: verifying
trigger: "Dock icon tooltip text clipping issue - text gets cut off when hovering over dock navigation icons"
created: 2026-05-16T00:00:00Z
updated: 2026-05-16T13:45:00Z
symptoms_prefilled: true
goal: find_and_fix
checkpoint_response: |
  Issue NOT FIXED - Previous attempt removed max-w-[150px] and truncate but tooltip text STILL clipping in live app. User reports same issue persists.
---

## Current Focus

hypothesis: Previous fix INCOMPLETE - removed inline width constraints but tooltip still clipping. Likely causes: (1) Parent DockItem clipping due to rounded-full + flex, (2) CSS cascade applying override, (3) Tooltip positioned inside clipped container rather than escaping it
test: Deep inspection of DockItem parent, all parent containers, and CSS specificity chain
expecting: Find what's actually constraining tooltip width after width constraints removed
next_action: Check all parent containers for overflow/clip rules; verify tooltip escapes clipping context; test with browser DevTools

## Symptoms

expected: |
  Hover over any dock icon → full tooltip text visible
  Text should not overflow container or viewport
  Text should wrap or truncate gracefully with ellipsis if needed

actual: |
  Hover over dock icons → tooltip text gets cut off mid-word
  Text appears clipped/truncated
  Remaining text hidden or overflowing

errors: |
  Text clipping observed in screenshot

started: Issue persists after previous dock fix attempt (magnification, alignment)

reproduction: |
  1. Load dashboard
  2. Hover mouse over any dock icon (home, camera, menu, calendar, chat)
  3. Observe tooltip text
  4. Text should be fully visible but is cut off

## Eliminated

(none yet)

## Evidence

## Evidence

- timestamp: 2026-05-16
  checked: DockLabel component in Dock.jsx (lines 46-68)
  found: |
    Multiple constraints causing clipping:
    1. className includes `max-w-[150px]` - hardcoded 150px max width
    2. className includes `whitespace-nowrap` - forces single line
    3. className includes `truncate` - adds overflow:hidden + text-overflow:ellipsis
    4. inline style has `overflow: 'hidden'` - hides content beyond bounds
    5. inline style has `maxWidth: '150px'` - redundant width constraint
    
    Combined effect: text longer than ~140px (accounting for px-2 padding) gets cut off
    Example: "Camera" label might display as "Cam..." instead of full text
  implication: |
    The 150px limit is artificial and too restrictive for longer labels.
    Solution: Remove max-width constraint, remove truncate class, 
    remove overflow:hidden from style to allow tooltip to expand naturally
    while keeping overflow:visible or clip to prevent viewport issues

- timestamp: 2026-05-16
  checked: Parent container structure in Dock.jsx
  found: |
    DockLabel is absolutely positioned (-top-6) within DockItem (relative positioned)
    DockItem doesn't have overflow:hidden
    Outer Dock containers use max-w-full and w-fit (no overflow constraints)
    No parent constraints that would clip tooltip positioned above dock
  implication: Tooltip can expand freely in all directions now that max-width removed

- timestamp: 2026-05-16
  checked: Fix applied to Dock.jsx
  found: |
    Removed from className: max-w-[150px] truncate
    Removed from style: maxWidth, overflow, textOverflow
    Kept: absolute positioning, z-50, centering with x:-50%, whitespace-nowrap
  implication: Tooltip now expands to fit content naturally

- timestamp: 2026-05-16 CHECKPOINT FAILURE
  checked: User reports tooltip STILL clipping in live app after previous fix
  found: |
    Previous fix removed direct DockLabel constraints but didn't account for parent clipping.
    Traced parent hierarchy:
    - DockLabel (absolute -top-6 left-1/2) → inside
    - DockItem (relative, rounded-full, no overflow-hidden visible) → inside
    - Dock outer div (mx-2, flex, max-w-full, no overflow) → inside
    - Dock inner div (flex, w-fit, gap-4, px-2, no overflow) → inside
    - GlassSurface component (App.jsx line 71) → **HAS overflow-hidden!**
  
  ROOT CAUSE FOUND:
  App.jsx wraps Dock in <GlassSurface> component (line 71)
  GlassSurface.jsx line 286 has class: 'overflow-hidden'
  This creates a clipping context that clips the absolutely-positioned tooltip
  The tooltip is a child of GlassSurface, so even though it's absolutely positioned
  with z-50, it still gets clipped by parent's overflow:hidden
  
  The overflow:hidden is intentional on GlassSurface (for glass-morphism effect with
  rounded borders), so we can't simply remove it. The tooltip needs to escape the
  clipping context by being rendered OUTSIDE the GlassSurface container.
  
  implication: |
    Must use React Portal to render tooltip at document root level, outside GlassSurface clipping context.
    This allows tooltip to escape the overflow:hidden constraint while keeping glass effect intact.

## Resolution

root_cause: |
  The Dock component is wrapped in GlassSurface (App.jsx line 71), which has 
  overflow:hidden CSS class applied for glass-morphism visual effect with rounded corners.
  
  The DockLabel tooltip was absolutely positioned inside DockItem (inside Dock → inside GlassSurface),
  creating a stacking context where the tooltip remained clipped by the parent's overflow:hidden
  constraint despite z-50 and other CSS fixes.
  
  The previous fix removed direct width/truncation constraints on DockLabel but didn't account
  for the parent GlassSurface clipping context. Once clipped by a parent's overflow:hidden,
  no amount of child CSS constraints matter - the browser's rendering pipeline clips at that
  point in the DOM hierarchy.

fix: |
  IMPLEMENTED: React Portal approach
  
  1. Added import: import { createPortal } from 'react-dom'
  
  2. Refactored DockLabel component:
     - Added labelRef to track the label's position in DOM
     - When tooltip becomes visible, calculate its position relative to viewport
     - Calculate top: rect.top - 30 (position above label)
     - Calculate left: rect.left + rect.width / 2 (center on label horizontally)
     - Changed positioning from absolute + x:-50% to fixed + transform:translateX(-50%)
     - Use createPortal() to render tooltip at document.body level (outside GlassSurface)
     - This bypasses the overflow:hidden clipping context entirely
  
  Benefits:
  - Tooltip rendered at document.body, escapes GlassSurface clipping
  - Maintains correct positioning via getBoundingClientRect() viewport calculations
  - No changes needed to GlassSurface (glass effect unaffected)
  - Tooltip can be arbitrarily wide - no parent constraints apply

verification: (pending - awaiting test in live app)
