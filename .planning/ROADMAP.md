# Roadmap: NutriSnap

## Overview

NutriSnap v1 rebuilds the project from a discarded demo app into a disciplined ML and inference pipeline: first make the data and repository structure trustworthy, then integrate FoodSAM and a hardware-feasible volume-estimation path, train a lightweight nutrition regressor, add validation safeguards, and finally ship the whole pipeline behind a production-style FastAPI interface with automated quality checks.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Data Contracts** - Rebuild the repo structure and create reproducible MVP dataset artifacts.
- [x] **Phase 2: Segmentation & Preprocessing** - Integrate FoodSAM and produce clean downstream-ready meal artifacts.
- [ ] **Phase 3: Volume Estimation Integration** - Adapt the chosen external volume-estimation path to NutriSnap inputs and hardware limits.
- [ ] **Phase 4: Nutrition Model & Ensemble** - Train the lightweight nutrition regressor and package ensemble inference.
- [ ] **Phase 5: Evaluation & Verification** - Add robust metrics, failure-mode checks, and prediction validation safeguards.
- [ ] **Phase 6: FastAPI Delivery & Quality Hardening** - Expose the production-style API and add automated quality gates.

## Phase Details

### Phase 1: Foundation & Data Contracts
**Goal**: Establish the rebuild-era project structure and create trustworthy dataset, split, and MVP-scope artifacts that all later phases can depend on.
**Depends on**: Nothing (first phase)
**Requirements**: [DATA-01, DATA-02, DATA-03, DATA-04, ENG-01]
**Success Criteria** (what must be TRUE):
  1. A reproducible ML-project layout exists for configs, data stages, source code, reports, results, and scripts.
  2. Nutrition5k ingestion and audit code can detect corruption or missing assets instead of silently proceeding.
  3. Official train/test boundaries, MVP dish subset selection, and 5-fold CV artifacts can be regenerated from code.
  4. The repository's structure and docs clearly reflect the rebuild architecture rather than the retired demo app.
**Plans**: 3 plans

Plans:
- [x] 01-01: Replace the legacy app-centric scaffold with the config-driven ML project layout and baseline developer tooling.
- [x] 01-02: Implement Nutrition5k audit, ingestion, subset-selection, and leakage-safe split generation workflows.
- [x] 01-03: Persist CV artifacts, manifests, and setup documentation required by all downstream phases.

### Phase 2: Segmentation & Preprocessing
**Goal**: Produce reliable masked and normalized meal artifacts by integrating FoodSAM and the rebuild preprocessing pipeline.
**Depends on**: Phase 1
**Requirements**: [SEGM-01, SEGM-02, SEGM-03]
**Success Criteria** (what must be TRUE):
  1. FoodSAM can be invoked from the NutriSnap repo to generate usable meal masks for representative samples.
  2. The RGB preprocessing path runs after segmentation and outputs normalized artifacts for training and inference.
  3. Downstream geometry- or depth-compatible intermediates are generated in a format the volume-estimation adapter can consume.
**Plans**: 3 plans

Plans:
- [x] 02-01: Add FoodSAM dependency management plus a thin NutriSnap wrapper/adapter layer.
- [x] 02-02: Implement reproducible masked RGB preprocessing and dataset transforms for training and inference.
- [x] 02-03: Build artifact-generation scripts for geometry/depth-compatible intermediates and sample smoke checks.

### Phase 3: Volume Estimation Integration
**Goal**: Integrate the external volume-estimation path, with FoodVolume as the MVP default, and convert its outputs into stable model features.
**Depends on**: Phase 2
**Requirements**: [VOL-01, VOL-02]
**Success Criteria** (what must be TRUE):
  1. The chosen external volume-estimation component runs on representative NutriSnap inputs through a project-owned adapter layer.
  2. Volume outputs are converted into metric volume, area, and quality metadata ready for training and inference.
  3. Benchmarking confirms the MVP path can operate within GTX 1650 / 4GB constraints or clearly documents the fallback boundaries.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Build the FoodVolume-first adapter layer and dependency strategy for NutriSnap inputs and outputs.
- [ ] 03-02: Normalize external outputs into reusable scalar features and quality metadata for downstream modeling.
- [ ] 03-03: Benchmark hardware fit, record tradeoffs, and keep VolETA scoped as an optional benchmark/reference path.

### Phase 4: Nutrition Model & Ensemble
**Goal**: Train and package the lightweight nutrition regressor and ensemble workflow that turns visual plus scalar features into macro predictions.
**Depends on**: Phase 3
**Requirements**: [MODL-01, MODL-02, MODL-03]
**Success Criteria** (what must be TRUE):
  1. A lightweight model can train on target hardware to predict calories, protein, carbohydrates, and fats.
  2. Mixed precision, gradient accumulation, or equivalent controls keep training within the 4GB memory budget.
  3. Five-fold training artifacts and ensemble inference behavior can be produced reproducibly from code and config.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Implement the nutrition regressor architecture, feature assembly, and training configuration.
- [ ] 04-02: Build the training loop, checkpointing, and fold-management workflow for cross-validation.
- [ ] 04-03: Package ensemble inference so trained folds can be used consistently by evaluation and API delivery.

### Phase 5: Evaluation & Verification
**Goal**: Prove the model is trustworthy by measuring the right metrics, detecting failure modes, and validating output realism.
**Depends on**: Phase 4
**Requirements**: [MODL-04, MODL-05, VERI-01, VERI-02]
**Success Criteria** (what must be TRUE):
  1. Evaluation reports MAE, MAPE, R², Spearman, bias, and ensemble-variance diagnostics for trained candidates.
  2. Constant-prediction and obvious overfitting failure modes are surfaced explicitly instead of slipping through summary metrics.
  3. Rule-based nutrition validation can block or flag implausible outputs before they reach API consumers.
  4. Optional LLM fallback behavior can be enabled for flagged cases and records its verification outcome.
**Plans**: 3 plans

Plans:
- [ ] 05-01: Implement evaluation reports and diagnostics for target metrics and failure-mode detection.
- [ ] 05-02: Build the rule-based validator and threshold/config management for nutrition realism checks.
- [ ] 05-03: Add the optional LLM fallback path and verification metadata/audit handling.

### Phase 6: FastAPI Delivery & Quality Hardening
**Goal**: Ship the full pipeline behind a production-style FastAPI interface and protect it with automated quality checks.
**Depends on**: Phase 5
**Requirements**: [API-01, API-02, API-03, ENG-02]
**Success Criteria** (what must be TRUE):
  1. `POST /predict` accepts a meal image and returns an accepted job identifier without blocking on full inference.
  2. `GET /result/{image_id}` returns processing/completed states and includes predictions plus verification metadata when ready.
  3. Representative end-to-end inference stays at or below 2 seconds per image, or any bounded exception is measured and documented.
  4. Automated linting and tests cover the core pipeline and API behavior needed to release with confidence.
**Plans**: 3 plans

Plans:
- [ ] 06-01: Implement the FastAPI inference service, background execution flow, and result-store contract.
- [ ] 06-02: Wire the trained pipeline into `/predict` and `/result/{image_id}` with response schemas and performance tuning.
- [ ] 06-03: Add automated tests, lint/CI automation, and release-readiness documentation for the shipped backend.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Contracts | 3/3 | Completed | 2026-04-11 |
| 2. Segmentation & Preprocessing | 3/3 | Completed | 2026-04-12 |
| 3. Volume Estimation Integration | 0/3 | Not started | - |
| 4. Nutrition Model & Ensemble | 0/3 | Not started | - |
| 5. Evaluation & Verification | 0/3 | Not started | - |
| 6. FastAPI Delivery & Quality Hardening | 0/3 | Not started | - |
