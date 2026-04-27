# Phase 2 Plan: Intelligence & Analysis

## Objective
Integrate the multi-food inference engine using a sequential VRAM orchestration pattern, build an asynchronous ingredient mapping service, and launch the AI nutrition assistant. Ensure peak VRAM remains below 4GB.

## Tech Stack
- FastAPI (Backend)
- PyTorch (Inference - YOLOv5, SAM2, GLPN, ViT)
- Gemini 2.0 Flash (Validation & Assistant)
- CSV (Ingredient Mapping)
- WebSockets (Real-time Chat)

## Wave Structure

| Wave | Plans | Autonomous | Objective |
|------|-------|------------|-----------|
| 1 | 02-01 | Yes | YOLOv5 Integration & VRAM Orchestration |
| 2 | 02-02, 02-03 | Yes | Async Tasks & Ingredient Mapping |
| 3 | 02-04 | Yes | AI Assistant & Gemini Validation |
| 4 | 02-05 | Yes | Frontend Display & Chat UI |

## Tasks
- [ ] **02-01: Multi-Food Inference Integration** (Wave 1)
  - Replace YOLOv8 with YOLOv5 for lower overhead.
  - Implement `SequentialOrchestrator` for Load-Run-Unload pattern.
  - Update `main.py` lifespan to remove legacy startup model loading.
- [ ] **02-02: Async Task Management** (Wave 2)
  - Implement `AsyncTaskManager` for background inference tracking.
  - Create status polling endpoints.
- [ ] **02-03: Ingredient Mapping Service** (Wave 2)
  - Create singleton `MappingService` with CSV database and fuzzy matching.
  - Enrich pipeline results with ingredient breakdowns.
- [ ] **02-04: AI Nutrition Assistant** (Wave 3)
  - Integrate Gemini 2.0 Flash for common-sense validation.
  - Contextualize ChatBot with user profile and meal history.
- [ ] **02-05: Frontend Integration** (Wave 4)
  - Build `usePrediction` polling hook.
  - Implement `MultiFoodDisplay` and `ChatBot` components.

## Verification
- [ ] **VRAM Check**: Peak usage < 4GB during full inference.
- [ ] **Automated Tests**: Pytest suite for mapping, task manager, and API flow.
- [ ] **E2E Flow**: Full image-to-itemized-result-to-chat interaction.

See [02-VALIDATION.md](./02-VALIDATION.md) for detailed test architecture.
