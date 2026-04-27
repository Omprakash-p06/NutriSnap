# AGENTS

## Project

**NutriSnap**

NutriSnap is a lightweight, production-oriented AI system that estimates calories, protein, carbohydrates, and fats from a single meal photo. The active project direction is the rebuild described in `misc/ARCHITECTURE.md`, `misc/revised architecture.mermaid`, `misc/revised_implementationplan.md`, and `misc/implementation_changes.md`, not the older demo app preserved in git history.

**Core value:** A user can upload a single meal image and receive a realistic nutrition estimate quickly enough for real-world use on commodity hardware.

## Constraints

- GTX 1650 with 4GB VRAM is the target hardware envelope.
- End-to-end inference should stay at or below 2 seconds per image.
- Target calorie accuracy is <= 65 kcal MAE and <= 30% MAPE.
- The system must avoid constant predictions and obvious overfitting failure modes.
- The architecture should remain a transparent modular pipeline, not a black-box end-to-end model.
- The deliverable is a production-style FastAPI backend.

## Source Of Truth

Read these first when working on the rebuild:

- `misc/ARCHITECTURE.md`
- `misc/revised architecture.mermaid`
- `misc/revised_implementationplan.md`
- `misc/implementation_changes.md`
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`

## Architecture Direction

- Use FoodSAM for segmentation.
- Prefer FoodVolume as the MVP volume-estimation path for the 4GB hardware target.
- Keep VolETA as a benchmark/reference path only if it proves feasible.
- Train the lightweight nutrition regressor as NutriSnap's custom model layer.
- Expose the system through asynchronous `POST /predict` and `GET /result/{image_id}` endpoints.
- Include a rule-based validator and optional LLM fallback for flagged outputs.

## Workflow

Before using file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Preferred entry points:

- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
