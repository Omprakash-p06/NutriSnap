# NutriSnap

## What This Is

NutriSnap is a lightweight, production-oriented AI system that estimates calories, protein, carbohydrates, and fats from a single meal photo. The project is being rebuilt from an earlier proof-of-concept into a modular computer vision pipeline that combines research-backed external segmentation and volume-estimation components with a custom lightweight nutrition regressor and a FastAPI backend, all targeted at a GTX 1650 with 4GB VRAM.

The current project source of truth is the rebuild plan captured in `misc/ARCHITECTURE.md`, `misc/revised architecture.mermaid`, `misc/revised_implementationplan.md`, and `misc/implementation_changes.md`. The previously committed full-stack demo app is useful historical context, but it is no longer the target architecture.

## Core Value

A user can upload a single meal image and receive a realistic nutrition estimate quickly enough for real-world use on commodity hardware.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can submit a single meal image and receive calorie, protein, carb, and fat estimates through a FastAPI backend.
- [ ] The inference pipeline uses a modular, research-backed architecture: segmentation, volume estimation, nutrition regression, and verification.
- [ ] The MVP operates within GTX 1650 / 4GB VRAM limits while avoiding constant predictions and obvious overfitting.
- [ ] The system exposes production-ready backend behavior, including asynchronous prediction handling and result retrieval.
- [ ] The project structure supports reproducible training, evaluation, debugging, and later model/component swaps.

### Out of Scope

- Native mobile or full consumer frontend product before the backend MVP is validated — backend/API correctness is the priority.
- Broad all-food coverage before proving the narrow 5-10 dish MVP subset — constrained scope is required for accuracy and feasibility.
- Training custom segmentation or 3D reconstruction systems from scratch for v1 — the plan is to integrate research-backed external repositories instead.
- Cloud-GPU-dependent deployment paths — the target system must remain practical on local constrained hardware.
- Barcode scanning or manual food entry as the core experience — visual estimation from an image is the differentiator.

## Context

The repository originally contained a full-stack demo app with a FastAPI backend, React frontend, and locally managed AI pipeline. The current worktree intentionally moves away from that implementation toward a cleaner research-backed rebuild.

The rebuild plan centers on:
- a narrow, high-accuracy MVP built on 5-10 selected dish types
- FoodSAM for segmentation
- external volume-estimation tooling, with FoodVolume preferred for the GTX 1650 / 4GB target and VolETA retained as a higher-end reference path
- a custom lightweight nutrition regressor that consumes food-class and portion/volume features
- a verification layer combining hard rules with optional LLM fallback
- a FastAPI backend that supports real-world inference usage

Training and evaluation are expected to use Nutrition5k-related assets and preprocessing references from external repositories such as DietAI24 and Nutrition5k utilities. Runtime input must remain a single 2D image even if some reference implementations or datasets use RGB-D pairs or multi-view assumptions; that adaptation risk is part of the project work.

## Constraints

- **Hardware**: GTX 1650 with 4GB VRAM — the architecture, training strategy, and third-party integrations must stay within consumer-grade GPU limits.
- **Performance**: Inference time must stay at or below 2 seconds per image — the system needs to feel usable, not just accurate offline.
- **Accuracy**: Target calorie MAE is <= 65 kcal and calorie MAPE is <= 30% — success is tied to useful nutritional estimates, not just qualitative demos.
- **Reliability**: No constant predictions and strong safeguards against overfitting — model behavior must remain believable and debuggable.
- **Architecture**: The solution must use a transparent modular pipeline, not a black-box end-to-end model — explainability and replaceability matter.
- **Deployment**: The deliverable must be a FastAPI backend suitable for production-style use — API design and runtime stability are required, not optional.
- **Dependencies**: External repositories must be integrated carefully and reproducibly — third-party code is a strength only if dependency management stays controlled.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rebuild NutriSnap as a modular CV pipeline instead of extending the old monolithic demo app | The new goal prioritizes research-backed components, clearer boundaries, and production readiness | — Pending |
| Use FoodSAM as the segmentation solution | It replaces custom segmentation work with a specialized, research-backed food segmentation approach | — Pending |
| Prefer FoodVolume as the primary volume-estimation path for the MVP | The hardware target is GTX 1650 / 4GB, and the planning docs identify FoodVolume as the lighter-weight fit | — Pending |
| Keep VolETA as a reference or stretch integration path, not the default MVP dependency | It is stronger in capability but heavier in dependencies and GPU expectations | — Pending |
| Train only the lightweight nutrition mapping model as custom project IP | This keeps scope focused on the part that directly delivers NutriSnap's unique value | — Pending |
| Use asynchronous `/predict` and `/result/{image_id}` backend behavior | The architecture should avoid blocking heavy inference requests and support real-world API use | — Pending |
| Add a rule-based validator plus optional LLM fallback | Nutrition outputs need a realism/safety layer beyond raw model prediction | — Pending |
| Start with a narrow 5-10 dish subset before expanding food coverage | Constrained scope improves accuracy, reduces overfitting risk, and fits the prototype goal | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-11 after initialization*
