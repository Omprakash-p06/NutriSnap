# Phase 1: Infrastructure: User Profiles - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish health profiles and daily macro targets. Excludes dynamic macro calculation over-time (handled in later meal-planner phases).
</domain>

<decisions>
## Implementation Decisions

### Macro Distribution Options
- **D-01:** Hardcode standard 30/40/30 split (Protein/Carbs/Fats). Do not build UI for custom selection yet.

### Measurement Units
- **D-02:** Strictly enforce Metric (kg/cm) on the backend and frontend to simplify math. Imperial support deferred.

### Goal Magnitude
- **D-03:** Stick to static baseline deficit/surplus modifiers (lose = -500 kcal, gain = +300 kcal, maintain = 0 kcal).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation Structure
- `backend/models/user.py` — Existing DB schema for users
- `frontend/src/pages/Profile.tsx` — Existent local calculation logic
</canonical_refs>

---
*Phase: 1-infrastructure-user-profiles*
*Context gathered: 2026-03-31 via gsd-discuss-phase*
