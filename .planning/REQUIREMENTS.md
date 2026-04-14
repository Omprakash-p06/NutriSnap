# Requirements: NutriSnap

**Defined:** 2026-04-11
**Core Value:** A user can upload a single meal image and receive a realistic nutrition estimate quickly enough for real-world use on commodity hardware.

## v1 Requirements

### Data Foundation

- [ ] **DATA-01**: Developer can ingest and audit Nutrition5k source assets into a reproducible `raw -> interim -> processed` data flow without silently accepting corrupt or missing files.
- [ ] **DATA-02**: Developer can reproduce official train/test split handling without leaking dish instances across dataset boundaries.
- [ ] **DATA-03**: Developer can define and persist a narrow 5-10 dish MVP subset that becomes the training and evaluation scope for v1.
- [ ] **DATA-04**: Developer can generate a validation split and 5-fold stratified group cross-validation artifacts for the MVP subset.

### Segmentation & Preprocessing

- [ ] **SEGM-01**: System can generate food masks for target meal images using an integrated FoodSAM-based segmentation step.
- [ ] **SEGM-02**: System can apply reproducible RGB preprocessing after segmentation, including denoising, contrast enhancement, resizing, and normalization.
- [ ] **SEGM-03**: System can prepare the geometry- or depth-compatible artifacts required by the chosen volume-estimation path and downstream nutrition regressor.

### Volume Estimation

- [x] **VOL-01**: System can estimate meal portion or volume through a research-backed external component adapted to NutriSnap's input and data formats.
- [x] **VOL-02**: System can convert the volume-estimation output into metric volume, area, and quality metadata that downstream training and inference can consume within GTX 1650 / 4GB constraints.

### Nutrition Model

- [x] **MODL-01**: Developer can train a lightweight nutrition regressor that predicts calories, protein, carbohydrates, and fats from visual and scalar features.
- [x] **MODL-02**: Training can run on the target hardware using mixed precision, gradient accumulation, or equivalent memory-control techniques.
- [x] **MODL-03**: System can run 5-fold cross-validation and ensemble inference for the nutrition regressor.
- [x] **MODL-04**: Evaluation can detect constant-prediction or obvious overfitting failure modes instead of reporting misleadingly good averages.
- [x] **MODL-05**: Evaluation reports calorie MAE, calorie MAPE, R², Spearman correlation, bias, and ensemble-variance metrics for each trained candidate.

### Verification

- [x] **VERI-01**: System applies rule-based nutrition validation before returning predictions, including hard bounds and calorie-macro consistency checks.
- [ ] **VERI-02**: System can optionally invoke an LLM fallback or second-opinion step when rule checks fail or model uncertainty crosses a configured threshold.

### API Delivery

- [ ] **API-01**: Client can submit a meal image to `POST /predict` and receive an accepted job identifier immediately.
- [ ] **API-02**: Client can poll `GET /result/{image_id}` until prediction output and verification status are ready.
- [ ] **API-03**: Completed API responses include nutrient estimates, verification outcome, and enough metadata to support downstream UI display and debugging, with representative inference staying at or below 2 seconds per image.

### Engineering Quality

- [ ] **ENG-01**: The repository follows a reproducible ML-project structure with config-driven runs, scripts, reports, and documented artifacts that match the rebuild architecture.
- [ ] **ENG-02**: Automated linting and test checks exist for the core pipeline and API behavior so regressions are caught before release.

## v2 Requirements

### Product Expansion

- **PROD-01**: System supports a broader food taxonomy beyond the initial 5-10 dish MVP subset.
- **PROD-02**: Users can access a polished end-user application layer beyond the backend MVP.
- **PROD-03**: System supports personalized diet planning, recipe recommendation, or related nutrition-adjacent features.

### Infrastructure Expansion

- **INFR-01**: System supports more scalable deployment paths beyond the initial single-node constrained-hardware target.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native mobile app as a first deliverable | Backend and ML correctness are the immediate priorities |
| Broad all-food generalization in v1 | MVP scope is intentionally limited to 5-10 dish types for accuracy and feasibility |
| Training custom segmentation or 3D reconstruction models from scratch | The architecture intentionally reuses research-backed external repositories |
| Cloud-GPU-only solution | The project must remain viable on GTX 1650 / 4GB hardware |
| Barcode scanning or manual logging as the primary workflow | NutriSnap's differentiator is visual estimation from a meal image |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| SEGM-01 | Phase 2 | Pending |
| SEGM-02 | Phase 2 | Pending |
| SEGM-03 | Phase 2 | Pending |
| VOL-01 | Phase 3 | Completed |
| VOL-02 | Phase 3 | Completed |
| MODL-01 | Phase 4 | Completed |
| MODL-02 | Phase 4 | Completed |
| MODL-03 | Phase 4 | Completed |
| MODL-04 | Phase 5 | Completed |
| MODL-05 | Phase 5 | Completed |
| VERI-01 | Phase 5 | Completed |
| VERI-02 | Phase 5 | Pending |
| API-01 | Phase 6 | Pending |
| API-02 | Phase 6 | Pending |
| API-03 | Phase 6 | Pending |
| ENG-01 | Phase 1 | Pending |
| ENG-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-11*
*Last updated: 2026-04-11 after roadmap creation*
