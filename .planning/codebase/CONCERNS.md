# Project Concerns & Risks

**Refresh Date:** 2026-04-27

## Technical Risks

**Model Accuracy:**
- **Risk:** Achieving MAE ≤ 40 kcal across diverse lighting and angles is challenging.
- **Mitigation:** Heavy reliance on SAM 2 for precise masking and Gemini for final validation logic.

**Inference Latency:**
- **Risk:** The multi-stage pipeline (YOLO -> SAM 2 -> GLPN -> ViT -> LLM) may exceed the 200ms target on non-GPU hardware.
- **Mitigation:** Using `sam2-hiera-tiny` and optimizing image resizing before processing.

**LLM Cost & Rate Limits:**
- **Risk:** Scaling the product with Gemini validation on every scan will incur significant costs.
- **Mitigation:** Use local models for primary inference and reserve LLMs for high-uncertainty cases.

## Architectural Bottlenecks

**Serial Background Worker:**
- **Issue:** The current job worker processes requests sequentially.
- **Impact:** High latency for concurrent users.
- **Future:** Move to Celery/Redis for parallel task distribution.

**Database Scalability:**
- **Issue:** Current local MongoDB/SQLite setup is not suitable for high-scale multi-region deployment.
- **Future:** Migrate to managed MongoDB Atlas or a distributed PostgreSQL.

## Maintenance & Fragility

**Dependency Drift:**
- **Issue:** High number of ML libraries (torch, ultralytics, transformers) leads to frequent breaking changes in underlying APIs.
- **Mitigation:** Pin specific versions in `requirements.txt`.

**Environment Setup:**
- **Issue:** Setting up CUDA and specific ML weights remains a manual and error-prone process.
- **Mitigation:** Move toward Dockerization of the inference service.

## Security

**Unprotected Endpoints:**
- **Risk:** Public API endpoints lack robust JWT authentication.
- **Mitigation:** Implementation of Auth0 or custom JWT layer is prioritized for Phase 12.
