# Phase 6 Research: FastAPI Delivery & Quality Hardening

This research investigates the technical stack and patterns required to deliver NutriSnap as a robust, production-style API within a <2s latency budget on constrained hardware.

## Standard Stack

| Component | Library | Rationale |
| :--- | :--- | :--- |
| **API Framework** | FastAPI | Async excellence, automatic OpenAPI docs, and lightweight. |
| **Data Validation** | Pydantic v2 | High-performance schema validation and type safety. |
| **Task Persistence** | SQLite (aiosqlite) | Lightweight, single-file DB suitable for local/edge deployment. |
| **Background Processing** | FastAPI `BackgroundTasks` | avoids Celery/Redis overhead for a lightweight single-node system. |
| **Testing** | `pytest` + `httpx` | Robust async integration testing. |

## Architecture Patterns

### Asynchronous Job Pattern
To satisfy **API-01** (Immediate Response) and **API-02** (Polling):
1. **POST /predict**: 
   - Assigns a unique `image_id` (UUID).
   - Writes task record to SQLite with status `PENDING`.
   - Spawns a non-blocking `BackgroundTask` to run the CV pipeline.
   - Returns Job ID immediately.
2. **GET /result/{image_id}**:
   - Returns JSON with current status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
   - Includes results if `COMPLETED`.

### GPU Serialization
To prevent VRAM contention on the 4GB GTX 1650:
- Use an `asyncio.Lock()` to ensure only one image is processed by the heavy ML pipeline at a time.
- Queue subsequent requests in memory via the `BackgroundTasks` system or a simple `asyncio.Queue`.

## Don't Hand-Roll

- **Multipart/Form-Data Handling**: Use FastAPI's builtin `UploadFile`.
- **JSON Serialization**: Use Pydantic's `.model_dump()`.
- **Locking**: Use `asyncio.Lock` instead of custom semaphores.

## Common Pitfalls

- **Thread-blocking CV calls**: OpenCV or Torch calls are CPU-bound and can block the event loop. Always run heavy sync calls in `run_in_executor`.
- **VRAM Leakage**: Ensure `torch.cuda.empty_cache()` is used if necessary between major pipeline steps, or stick to a persistent model process.
- **Stale Files**: Temporary uploads must be cleaned up after processing or after a TTL.

## Code Examples

### Job Orchestrator
```python
@app.post("/predict")
async def predict(file: UploadFile, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    await store.create_job(job_id)
    background_tasks.add_task(process_pipeline, job_id, file.file.read())
    return {"job_id": job_id, "status": "accepted"}
```

### Async/Sync Boundary
```python
def run_heavy_inference(model, data):
    with torch.no_grad():
        return model(data)

# In the async worker:
result = await asyncio.get_event_loop().run_in_executor(None, run_heavy_inference, model, data)
```
