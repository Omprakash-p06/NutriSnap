# Roadmap: NutriSnap

## Global Process Standards

To ensure project integrity and maintainability, the following standards apply to all phases and debug sessions:

1. **Pre-Execution Project Understanding**: Thoroughly understand the project's "North Star" context, purpose, and constraints before initiating any changes or starting execution of a phase.
2. **Comprehensive Mapping**: Always map the codebase and understand the entire structure before making changes during a phase.
3. **Atomic GitHub Commits**: Commit all changes to GitHub immediately after all tests pass at the end of each phase or debug session.
4. **Post-Action Codebase Mapping**: Run `/gsd-map-codebase` after each phase and debug session to refresh the codebase documentation.
5. **Architecture Synchronization**: The [nutrisnap_pipeline_2026-04-16.svg](file:///c:/Users/HP/Downloads/Nutrisnap/NutriSnap/misc/nutrisnap_pipeline_2026-04-16.svg) must be updated to reflect the latest architecture after every phase or debug session.
6. **Continuous Quality Verification**: Perform code quality checks (linting, static analysis) and run GitHub workflow tests during the execution of each phase to ensure no regressions.

---

## Phase 1: Core Engine & Foundation (P0)
**Goal**: Wrap the existing model into a usable API and establish the user management layer.
- [x] Phase 1.1: Project scaffolding (Backend & Frontend boilerplate).
- [x] Phase 1.2: Model Wrapper Service (FastAPI + EfficientNet/SAM2/GLPN integration).
- [x] Phase 1.3: Auth & Profile System (JWT + User Data + Mifflin-St Jeor).
- [x] Phase 1.4: Manual Logging & Database Setup (CRUD + USDA/JSON Lookup).

## Phase 2: Intelligence & Analysis (P1)
**Goal**: Add multi-food capability, ingredient breakdown, and AI reasoning.
**Plans:** 5 plans
- [x] 02-01-PLAN.md — YOLOv5 & Sequential VRAM Orchestration [INTELL-01]
- [x] 02-02-PLAN.md — Async Status Polling & Task Management [INTELL-04]
- [x] 02-03-PLAN.md — Ingredient Mapping Service (CSV-based breakdown) [INTELL-02]
- [x] 02-04-PLAN.md — AI Nutrition Assistant (Gemini API & Reasoning) [INTELL-03]
- [x] 02-05-PLAN.md — Frontend Multi-Food & Chat Integration [INTELL-05]

## Phase 3: UX & Personalization (P2)
**Goal**: Finalize the user experience with planning and visualizations.
**Plans:** 4 plans
- [ ] 03-01-PLAN.md — Meal Planner Engine (Rule-based Suggestion) [REQ-P2-01]
- [ ] 03-02-PLAN.md — Offline Aggregation & Dexie Setup [REQ-P2-02]
- [ ] 03-03-PLAN.md — Progress Dashboard & Visualizations [REQ-P2-02]
- [ ] 03-04-PLAN.md — PWA Polish & E2E Integration [NFR-03]

---
*Roadmap updated: 2026-04-28*
