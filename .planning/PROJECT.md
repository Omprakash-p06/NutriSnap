# Project: NutriSnap

## Context & Core Value
NutriSnap is an intelligent AI-powered meal planner application. Its core value is helping users seamlessly maintain a healthy lifestyle by effortlessly analyzing food images to track daily nutrition intake against personalized health goals.

## What This Is
- A React SPA frontend with a FastAPI/Python backend.
- A computer-vision pipeline (YOLOv8 + XGBoost) for food detection and portion estimation.
- An intelligent assistant that validates meals and curates daily diet plans using the Grok API.

## Requirements

### Validated
- ✓ [Core System] Image upload from frontend to FastAPI backend.
- ✓ [AI Pipeline] YOLOv8 detects food items and bounding boxes.
- ✓ [AI Pipeline] XGBoost + Depth estimation calculates portion sizes in grams.
- ✓ [AI Pipeline] Local JSON lookup estimates base nutrition (calories, protein, carbs, fats).

### Active
- [ ] [Validation] Integrate Grok API to verify and refine baseline nutritional estimates.
- [ ] [User Profiles] Allow users to input BMI and primary health goals (Weight Loss, Gain, Maintain).
- [ ] [Evaluation] System evaluates user's logged meals against their specific daily targets.
- [ ] [Tracking] Persist and display a continuous daily timeline of nutrition vs targets.
- [ ] [Meal Planning] Automatically generate customized meal plans and proactive diet suggestions using AI.

### Out of Scope
- [Feature] Calorie counting from barcodes (Focus is entirely on computer vision and AI).
- [Feature] Social sharing (Focus is on personal tracking and AI planning).

## Key Decisions
| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Grok API for validation | Provides high-accuracy semantic checking beyond simple hardcoded JSON datasets. | Pending |

## Evolution
This document evolves at phase transitions and milestone boundaries.
