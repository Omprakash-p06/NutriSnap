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
- [ ] Phase 2.1: YOLOv5 Multi-Food Detection Integration.
- [ ] Phase 2.2: Ingredient Mapping Service (CSV-based breakdown).
- [ ] Phase 2.3: AI Nutrition Assistant (Gemini API Integration).

## Phase 3: UX & Personalization (P2)
**Goal**: Finalize the user experience with planning and visualizations.
- [ ] Phase 3.1: Rule-based Meal Planner Engine.
- [ ] Phase 3.2: Progress Dashboard (Recharts + Intake Tracking).
- [ ] Phase 3.3: Final E2E Integration & Polish.

---
*Roadmap initialized: 2026-04-27*
