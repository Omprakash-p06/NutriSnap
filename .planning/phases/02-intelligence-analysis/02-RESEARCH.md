# Phase 2: Intelligence & Analysis Research

## Standard Stack
- **Inference Integration**: PyTorch 2.x, FastAPI `BackgroundTasks`, `anyio` for thread pooling.
- **VRAM Management**: Sequential model loading/unloading using `model.cpu()`, `del`, and `torch.cuda.empty_cache()`.
- **Ingredient Mapping**: Python `csv` module, `pandas` (optional for large datasets), and a singleton `MappingService` class.
- **AI Assistant**: FastAPI `WebSockets`, Google Generative AI Python SDK (Gemini 2.0 Flash), Pydantic for message schemas.

## Architecture Patterns
### 1. Sequential Inference Pipeline
Since the environment is constrained to 4GB VRAM, the pipeline must follow a "Load-Run-Unload" pattern for each major model.
- **Stage 1**: YOLOv8 (Detection) -> ~100MB VRAM
- **Stage 2**: SAM 2 (Segmentation) -> ~300MB VRAM (Tiny version)
- **Stage 3**: GLPN (Depth) -> ~400MB VRAM
- **Stage 4**: ViT Mass Regressor -> ~800MB VRAM
- **Verification**: Gemini 2.0 Flash (API-based, 0 VRAM)

### 2. Async Task Flow
FastAPI should return a `202 Accepted` response with a `task_id` for inference requests. The inference runs in a `BackgroundTask`.
- Frontend polls `/status/{task_id}` or listens to a WebSocket for completion.

### 3. Singleton Mapping Service
Load the CSV database into a dictionary at startup. This allows O(1) lookups and ensures the memory overhead of the database is minimal and fixed.

### 4. Ingredient Mapping CSV Schema
Standard format for the `ingredients.csv` file:
```csv
food_name,ingredients,primary_category,calories_per_100g,protein_g,carbs_g,fats_g
"Pizza","dough, cheese, tomato sauce, oregano","Main Course",266,11.4,33.3,10.0
"Burger","bun, patty, lettuce, tomato, onion, cheese","Fast Food",250,13.0,20.0,15.0
```
Lookup logic should use a case-insensitive dictionary for fast retrieval.

## Don't Hand-Roll
- **VRAM Management**: Do not assume PyTorch handles garbage collection perfectly. Explicitly call `gc.collect()` and `torch.cuda.empty_cache()`.
- **WebSocket Protocol**: Use established message formats (e.g., JSON with `type`, `payload`).
- **Gemini Context**: Use the built-in `ChatSession` for history management instead of manually appending strings.

## Common Pitfalls
- **Memory Leaks**: Forgetting to move tensors to CPU before deleting the model can lead to leaked VRAM.
- **Blocking the Event Loop**: Running heavy inference directly in an `async def` function without `run_in_executor` or `BackgroundTasks` will freeze the API.
- **Database Scalability**: If the ingredient CSV grows beyond 100k rows, move to SQLite with an index on `food_name`.

## Code Examples

### VRAM Unloading Helper
```python
import torch
import gc

def unload_model(model):
    model.cpu()
    del model
    gc.collect()
    torch.cuda.empty_cache()
```

### Async Inference Task
```python
@app.post("/analyze")
async def analyze_food(file: UploadFile, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(run_inference_pipeline, task_id, file)
    return {"task_id": task_id, "status": "processing"}
```

### Gemini Nutritionist Prompt
```python
SYSTEM_PROMPT = """
You are NutriSnap AI, a knowledgeable and empathetic nutritionist. 
Your goal is to provide supportive, evidence-based advice.
Context: You have access to the user's profile and their recent meal logs.
Tone: Encouraging, professional, and concise.
"""
```
