# Project: NutriSnap

## Context & Vision
NutriSnap is an automated, culturally-inclusive, zero-friction nutrition tracking platform. Originally a college mini-project, it aims to solve the tediousness of manual calorie tracking by leveraging computer vision and AI.

The platform specializes in handling complex, multi-food meals (including mixed Indian/Asian cuisines) without requiring specialized depth sensors, making it accessible on standard laptops and cloud environments.

## Core Objective
**Build a production-ready web platform** that transforms meal photos into actionable nutritional data (mass, calories, macros, ingredients) and provides personalized health guidance via AI.

## Current Technical State (The Engine)
We have a pre-trained **food mass estimation model** (EfficientNet + SAM2 + GLPN + volume scalar + calibration) trained on the Nutrition5k dataset.
- **Performance:** MAE 46g, R² 0.43, Spearman 0.60.
- **Constraint:** **No retraining** of the core model is allowed. All work focuses on wrapping this engine into services and integrating auxiliary pre-trained models (YOLOv5, Gemini).

## Target Audience
- Individuals seeking zero-friction calorie and macro tracking.
- Users of Indian/Asian cuisines currently underserved by existing apps.
- Health-conscious users needing personalized meal planning and AI nutrition advice.

## Development Standards
The project adheres to the following rigorous development standards:
- **Test-Driven Commits:** GitHub commits are mandatory after all tests pass at the end of every phase or debug session.
- **Continuous Documentation:** The codebase map is refreshed using `/gsd-map-codebase` after every significant unit of work.
- **Architectural Integrity:** The [Pipeline SVG](file:///c:/Users/HP/Downloads/Nutrisnap/NutriSnap/misc/nutrisnap_pipeline_2026-04-16.svg) must be updated to match the latest implementation after each phase.
- **Context First:** Change requests must be preceded by a full structural mapping of the codebase to ensure consistency.

## Tech Stack (Planned)
- **Backend:** Python (FastAPI, Uvicorn, Motor/MongoDB).
- **Frontend:** React (Vite, Framer Motion, Recharts).
- **ML/CV:** Existing mass model, YOLOv5 (Pre-trained), Gemini 2.0 Flash API.
- **Auth:** JWT-based.
- **Database:** MongoDB.
