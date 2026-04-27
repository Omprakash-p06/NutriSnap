# Phase 1 Research: Core Engine & Foundation

**Status:** Completed
**Date:** 2026-04-28

## Executive Summary
Phase 1 focuses on building the production-ready foundation for NutriSnap. This involves wrapping the existing ML models in a high-performance FastAPI service, establishing a robust React PWA, and implementing a secure user management system.

## Standard Stack
- **Backend Framework:** FastAPI (with `pydantic-settings` for config).
- **ML Serving:** `torch` (Inference only), `torchvision`, `transformers`.
- **Authentication:** `python-jose` (JWT), `passlib[bcrypt]` (Hashing).
- **Database:** MongoDB with `motor` (Async driver).
- **Frontend:** React 19 + Vite 8 + `vite-plugin-pwa`.
- **Styling:** Vanilla CSS + `framer-motion`.

## Architecture Patterns

### 1. Model Lifecycle Management
- **Pattern:** Use FastAPI `lifespan` events to load models (SAM 2, GLPN, EfficientNet) into memory once at startup.
- **Optimization:** Use `torch.inference_mode()` and `model.eval()` to minimize memory and maximize speed.
- **Resource Management:** Given the "no retraining" constraint, ensure models are loaded onto the correct device (CUDA/CPU) based on available hardware.

### 2. User Management & BMR Calculation
- **Pattern:** Store user attributes (weight, height, age, sex, activity level) in MongoDB.
- **BMR Logic:** Implement the Mifflin-St Jeor equation:
  - $BMR_{male} = (10 \times weight) + (6.25 \times height) - (5 \times age) + 5$
  - $BMR_{female} = (10 \times weight) + (6.25 \times height) - (5 \times age) - 161$
- **TDEE:** Apply activity multipliers (1.2 to 1.9) to calculate daily targets.

### 3. PWA Scaffolding
- **Pattern:** `vite-plugin-pwa` with `registerType: 'autoUpdate'` for seamless updates.
- **Offline Strategy:** Cache essential assets (icons, manifest) for offline launch capability.

## Don't Hand-Roll
- **Auth Flow:** Use `OAuth2PasswordBearer` and established JWT validation patterns.
- **Image Processing:** Use `Pillow` or `torchvision.transforms` for consistent preprocessing.
- **Validation:** Use `Pydantic` models for all API request/response validation.

## Common Pitfalls
- **Blocking Inference:** Running heavy ML models directly in `async` endpoints can block the event loop. **Solution:** Use `starlette.concurrency.run_in_threadpool` or a dedicated background task worker.
- **VRAM Exhaustion:** Loading multiple large models (SAM 2 + GLPN + EfficientNet) might exceed 4GB VRAM (RTX 3050 limit). **Solution:** Use `half()` precision or share memory where possible.
- **State Drift:** Ensure the frontend syncs its local state with the backend after logging or profile updates.

## Code Examples

### FastAPI Model Lifespan
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import torch

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models
    app.state.mass_model = torch.load("checkpoints/mass_model.pt").eval()
    yield
    # Clean up
    del app.state.mass_model

app = FastAPI(lifespan=lifespan)
```

### Mifflin-St Jeor Implementation
```python
def calculate_bmr(weight_kg, height_cm, age, sex):
    if sex.lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
```

## Next Steps
- Begin **Phase 1.1** with project scaffolding for both backend and frontend.
- Establish the database connection and basic Auth routes.
