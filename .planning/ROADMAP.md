# Roadmap: NutriSnap

## Overview

NutriSnap v1 builds a multi-layer accuracy pipeline: full RGB+Depth preprocessing, a three-stage pipeline (SAM 2 → GLPN → ViT), and a 3-tier verification layer (rule-based → Gemini API → optional USDA). Target: calorie MAE ≤ 40 kcal on Nutrition5k at ≤ 200ms inference per image on an RTX 3050.

See [`misc/strategy_final_2026-04-16.md`](../misc/strategy_final_2026-04-16.md) for the complete blueprint.

---

## Phase Summary

| Phase | Name | Status |
|-------|------|--------|
| 0 | Foundation Setup | ✅ Complete |
| 1 | Foundation & Data Pipeline | ✅ Complete |
| 2 | Foundation Preprocessing | ✅ Complete |
| 3 | SAM 2 -> GLPN -> ViT Pipeline | 🔄 In Progress |
| 4 | Full Dataset Training Run | ❌ Pending |
| 5 | Evaluation & Verification | ❌ Pending |
| 6 | FastAPI Delivery & Quality Hardening | ✅ Complete (API scaffolded) |
| 7 | User Auth, USDA Logs & Planning | ✅ Complete |
| 8 | AI Model Integration & Deployment | ✅ Complete |
| 9 | Final Polish & Performance Tuning | ✅ Complete |
| 10 | Frontend Integration & Global Testing | ❌ Pending |
| 11 | Multi-Food Detection & LLM Validation | 🔄 In Progress (2/4 plans) |

---

## Phase Details

### Phase 0: Foundation Setup ✅
**Goal**: Set up a clean, working backend foundation with proper project structure, database connection, and environment configuration for NutriSnap.  
**Requirements**: 
**Success Criteria**:
1. FastAPI app is initialized with robust root endpoint (`/`).
2. MongoDB async asyncIOMotorClient connected correctly via database.py.
3. Proper `requirements.txt` and `.gitignore` file are configured.

**Plans**: ✅ All complete
- [x] 00-01: FastAPI application setup & MongoDB connection configured.

---

### Phase 1: Foundation & Data Pipeline ✅
**Goal**: Reproducible ingest → audit → split artifacts.  
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, ENG-01  
**Success Criteria**:
1. Nutrition5k audit detects corruption/missing assets
2. Official train/test split respected (dish_id boundary)
3. 5-fold stratified CV artifacts generated from code
4. Reproducible `data/splits/` directory

**Plans**: ✅ All complete
- [x] 01-01: Repo structure, tooling baseline
- [x] 01-02: Ingest, audit, subset selection, split generation
- [x] 01-03: CV fold artifacts, manifests, setup docs

---

### Phase 2: Foundation Preprocessing ✅
**Goal**: Initial RGB+Depth processing and FoodSAM legacy masking.  
**Requirements**: PREP-01, PREP-02, PREP-03, SEGM-01  
**Success Criteria**:
1. Each dish → `{dish_id}_rgb.pt` and `{dish_id}_depth.pt` saved
2. Pipeline is resumable
3. FoodSAM (SAM 1) masking implemented

**Plans**: ✅ All complete
- [x] 02-01: FoodSAM integration and wrapper
- [x] 02-02: Bilateral+CLAHE+TELEA+Gaussian preprocessing
- [x] 02-03: Artifact generation scripts

---

### Phase 3: SAM 2 -> GLPN -> ViT Pipeline 🔄
**Goal**: Implement the 3-stage accuracy pipeline for MVP.  
**Requirements**: PREP-04, SEGM-02, MODL-01, MODL-02  
**Success Criteria**:
1. `FoodSegmenterSAM2` generates high-quality masks
2. `DepthEstimatorGLPN` recovers 3D structure from 2D images
3. Composite images (RGB+Mask+Depth) generated for 10-dish MVP subset
4. ViT-based mass regressor trained and achieving MAE ≤ 40 kcal

**Plans**: 🔄 In progress
- [x] 03-01: Implement SAM 2 and GLPN model adapters
- [ ] 03-02: Composite image generation and preprocessing update
- [ ] 03-03: ViT regressor implementation and training

---

### Phase 4: Full Dataset Training Run ❌
**Goal**: Run the 3-stage pipeline through 5-fold CV on the full Nutrition5k dataset.  
**Requirements**: ENS-01, ENS-02, DATA-05, DATA-06  
**Success Criteria**:
1. All dishes preprocessed to `data/processed/features/`
2. 5-fold model checkpoints saved
3. Ensemble inference running at ≤ 200ms per image

---

### Phase 5: Evaluation & Verification ❌
**Goal**: Prove the model is accurate; detection of failure modes; complete verification layer.  
**Requirements**: EVAL-01, EVAL-02, EVAL-03, VERI-01, VERI-02, VERI-03  
**Success Criteria**:
1. Reports: MAE, MAPE, R², RMSE, Bias, Spearman — per model and ensemble
2. Constant-prediction failure mode detected explicitly
3. Tier 3 USDA cross-reference implemented
4. Targets: cal MAE ≤ 40 kcal; MAPE ≤ 12%; R² ≥ 0.85; Spearman ≥ 0.90

---

### Phase 6: FastAPI Delivery & Quality Hardening ✅
**Goal**: Async job/poll API; quality gates.  
**Requirements**: API-01, API-02, API-03, ENG-02  
**Success Criteria**:
1. `POST /predict` accepts image, returns `image_id` immediately
2. `GET /result/{image_id}` returns nutritional estimates + verification metadata
3. Response includes confidence and Gemini fallback note
4. Inference ≤ 200ms normal; ≤ 3s with Gemini fallback

---

## Active Constraints

| Constraint | Value |
|-----------|-------|
| GPU | RTX 3050 / 4GB VRAM |
| Model | SAM 2 + GLPN + ViT-B/16 |
| Target MAE | ≤ 40 kcal |
| Target MAPE | ≤ 12% |
| Target inference | ≤ 200ms (normal) / ≤ 3s (Gemini) |

---
---

### Phase 7: User Auth, USDA Logs & Planning ✅
**Goal**: Implement user authentication, profile management, USDA food search, meal logging, and a personalized meal planning engine.
**Success Criteria**:
1. JWT-based authentication (register/login) is functional.
2. Users can search USDA FDC API and log meals.
3. Automated meal planning based on user BMR/TDEE goals.

**Plans**: ✅ All complete
- [x] 07-01: User Authentication & Profile Management
- [x] 07-02: USDA Food API & Manual Logging
- [x] 07-03: Personalized Meal Planning Engine

---

### Phase 8: AI Model Integration & Deployment ✅
**Goal**: Package the AI pipeline, expose it via a `/predict` endpoint, and prepare the system for cloud deployment.
**Success Criteria**:
1. AI pipeline is accessible via a Python module.
2. `POST /predict` returns nutrition estimates from uploaded images.
3. System is containerized and deployable to cloud platforms.

**Plans**: ✅ Complete
- [x] 08-01: Wrap Existing Model Pipeline into Reusable Module
- [x] 08-02: Create `/predict` Endpoint for Image Upload
- [x] 08-03: Integration Testing & Deployment Preparation

---

### Phase 9: Final Polish & Performance Tuning ✅
**Goal**: Harden the API for production — CORS, rate limiting, logging, real-time chat, and CI/CD.
**Success Criteria**:
1. Frontend can call all endpoints cross-origin with JWT auth.
2. API is rate-limited, consistently error-formatted, and observable.
3. WebSocket chat streams AI responses in real time.
4. CI/CD pipeline auto-deployments configured.

**Plans**: ✅ Complete
- [x] 09-01: CORS & API Documentation
- [x] 09-02: Rate Limiting & Error Handling
- [x] 09-03: Logging, Monitoring & Health Checks
- [x] 09-04: WebSocket for Real-time AI Chat
- [x] 09-05: CI/CD Pipeline & Final Deployment

---

### Phase 10: Frontend Integration & Global Testing ❌
**Goal**: Integrate the backend with the frontend application and perform end-to-end testing across all system components.
**Success Criteria**:
1. Frontend application fully connected to backend APIs.
2. E2E tests pass for core user journeys (login, upload, log).
3. Performance benchmarks met in integrated environment.

---

### Phase 11: Multi-Food Detection & LLM Validation Pipeline 🔄
**Goal**: Implement a YOLOv8-based multi-food detection system with an LLM validation layer to handle complex plates and improve accuracy.
**Requirements**: MULTI-01, MULTI-02, MULTI-03, MULTI-04, MULTI-05
**Success Criteria**:
1. Multi-food detection system (YOLOv8) integrated into the backend.
2. Prediction merger combining detection results with mass estimation.
3. LLM validation layer (OpenRouter/Gemini) verifying meal realism.
4. Final validated result returned via `/predict-validated` endpoint.

**Plans**: 4 plans
- [x] 11-01-PLAN.md — YOLOv8 Integration & Box-Prompted SAM 2 ✅
- [x] 11-02-PLAN.md — Multi-Food Prediction Merger & Mass Logic ✅
- [ ] 11-03-PLAN.md — LLM Validation Layer (Safety Net)
- [ ] 11-04-PLAN.md — Validated Prediction API Endpoint

---
*Roadmap updated: 2026-04-26 — Added Phase 10 & 11*
