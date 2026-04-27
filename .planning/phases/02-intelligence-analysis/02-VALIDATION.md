# Phase 2 Validation: Intelligence & Analysis

## Test Architecture

Phase 2 introduces complex multi-model pipelines and asynchronous task management. Validation follows a multi-tier approach to ensure stability and accuracy within resource constraints (4GB VRAM).

### 1. Unit Testing (Pytest)
- **Mapping Service**: Verify fuzzy matching logic and CSV data integrity.
- **Task Manager**: Ensure task state transitions (`pending` -> `processing` -> `completed`/`failed`) are correctly handled.
- **VRAM Cleanup**: Mock torch/gc to verify `unload()` methods are called in the correct sequence.

### 2. Integration Testing (Pytest-Asyncio)
- **Sequential Pipeline**: End-to-end test of `SequentialOrchestrator` with mock models to verify flow logic.
- **Async API Flow**: Verify `POST /predict/validated` returns 202 and `GET /predict/status/{id}` eventually returns 200 with results.
- **WebSocket Chat**: Verify context injection and message exchange with Gemini.

### 3. Performance & Resource Validation
- **VRAM Monitor**: Script to track peak VRAM usage during a full inference run. Target: < 4GB.
- **Latency Benchmarks**: Measure time-to-first-response (202) and total inference time for multi-food images.

## Coverage Goals

| Module | Coverage Target | Critical Paths |
|--------|-----------------|----------------|
| `backend/nutrisnap/pipeline/orchestrator.py` | 90% | Sequential load/unload, error recovery |
| `backend/app/utils/tasks.py` | 100% | Task state persistence, task expiration |
| `backend/app/utils/mapping.py` | 85% | Fuzzy matching, CSV loading |
| `backend/app/routers/prediction.py` | 80% | Background task triggering, status polling |
| `backend/app/routers/chat.py` | 75% | WebSocket connection, Gemini context injection |

## Verification Commands

```bash
# Run all Phase 2 backend tests
pytest backend/tests/phase2/

# Run specific VRAM check
python backend/scratch/check_vram_usage.py

# Run frontend tests
npm test frontend/src/components/__tests__/Phase2/
```

## Success Criteria (Nyquist)
- All automated tests pass in CI environment.
- Peak VRAM verified at < 4GB on target hardware.
- 100% requirement coverage for INTELL-01 through INTELL-05.
