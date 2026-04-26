# Phase 11: Multi-Food Detection & LLM Validation - Research

**Researched:** 2026-04-26
**Domain:** Computer Vision (YOLOv8 + SAM 2) & LLM Validation (Gemini/OpenRouter)
**Confidence:** HIGH

## Summary

This phase implements a multi-layer pipeline to handle complex meal plates with multiple food items. The current single-plate regression model (EfficientNetV2-B0) is supplemented with a YOLOv8 detection layer and a SAM 2 instance segmentation layer. By identifying individual items, the system can map them to specific food densities and nutritional profiles, providing a much higher degree of accuracy for heterogeneous meals. A final LLM validation layer (Gemini 2.0 Flash or OpenRouter) acts as a "sanity check" to detect hallucinations or unrealistic predictions.

**Primary recommendation:** Use YOLOv8 bounding boxes as "prompts" for SAM 2 to generate precise instance masks, then estimate mass per item using Volume * Density before passing the aggregated results to an LLM for final validation.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `ultralytics` | 8.4.31 | YOLOv8 Detection | Industry standard for real-time object detection. |
| `transformers`| 5.4.0 | SAM 2 & GLPN | Provides optimized implementations of SAM 2 and Depth estimation. |
| `scipy` | 1.16.2 | Convex Hull | Standard for calculating volumes from 3D point clouds. |
| `google-generativeai` | Current | Gemini API | Native SDK for Gemini 2.0 Flash validation. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | 0.28.1 | OpenRouter API | Asynchronous HTTP client for LLM validation via OpenRouter. |
| `numpy` | 2.2.5 | Matrix Operations | Mask manipulation and IoU calculations. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| YOLOv8 | YOLOv10/v11 | Better performance, but YOLOv8 is more stable and has better community food weights. |
| OpenRouter | Direct OpenAI | Direct API is faster but OpenRouter allows easier model switching (GPT-4o vs Claude 3.5). |

**Installation:**
```bash
pip install ultralytics transformers httpx google-generativeai
```

## Architecture Patterns

### Recommended Project Structure
```
src/nutrisnap/
├── pipeline/
│   ├── multi_food.py      # New: Multi-food detection orchestrator
│   ├── merger.py          # New: Logic to combine YOLO/SAM/Reg results
├── verification/
│   ├── llm_validator.py   # Enhanced: LLM validation logic
└── api/
    └── routers/
        └── predict.py     # New: /predict-validated endpoint
```

### Pattern 1: Box-Prompted Segmentation
Instead of "Automatic Mask Generation" (point grids), use YOLOv8 bounding boxes to prompt SAM 2. This significantly reduces VRAM usage and ensures masks correspond directly to detected labels.

### Pattern 2: Density-Based Mass Estimation
For multi-food, the "Global Regressor" is less accurate than itemized calculation:
1.  **Volume (V):** From SAM 2 mask + GLPN depth.
2.  **Density (D):** Looked up via YOLO Class (e.g., "Pizza" -> 0.8 g/cm³).
3.  **Mass (M):** $V \times D$.
4.  **Refinement:** Use the Global Regressor output as a "Total Plate Bound" to scale individual estimates.

### Anti-Patterns to Avoid
- **Hand-Rolling NMS:** Don't implement Non-Maximum Suppression; use the native `ultralytics` results.
- **Nested Food Overcounting:** Avoid counting both "Pizza" and "Pepperoni" masks separately; implement a containment check.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Object Detection | Custom CNN | YOLOv8 | Pre-trained food weights are widely available; SOTA performance. |
| Mask Extraction | Manual Thresholding | SAM 2 (Box Prompt) | Handles varied lighting and overlapping items better. |
| JSON Recovery | Regex Cleanup | `pydantic` or existing pattern | Robustly handle LLM markdown/text noise. |

## Common Pitfalls

### Pitfall 1: Coordinate Scaling
**What goes wrong:** YOLOv8 detections are often on a different resolution than SAM 2 inputs.
**Prevention:** Always normalize coordinates or use `PIL.Image` sizes to map bounding boxes precisely to masks.

### Pitfall 2: Hallucinating LLM
**What goes wrong:** The LLM might "correct" a valid vision detection to something incorrect (e.g., mistaking a rare fruit for a common one).
**Prevention:** Provide the LLM with the visual detection confidence score and a "Self-Correction" prompt that requires reasoning.

### Pitfall 3: Latency
**What goes wrong:** Sequential processing (YOLO -> SAM x N -> GLPN -> LLM) exceeds 3s.
**Prevention:** Run GLPN and YOLO in parallel; batch SAM 2 prompts for multiple boxes in a single call.

## Code Examples

### YOLOv8 Box-Prompted SAM 2
```python
# Source: https://docs.ultralytics.com/models/sam-2/
from ultralytics import YOLO, SAM

# 1. Detect boxes
det_model = YOLO("yolov8n.pt") # Or food-specific model
results = det_model.predict("meal.jpg")
boxes = results[0].boxes.xyxy.cpu().numpy()

# 2. Prompt SAM 2
sam_model = SAM("sam2_t.pt")
masks = sam_model.predict("meal.jpg", bboxes=boxes)
```

### LLM Validation Prompt
```python
PROMPT_VALIDATION = """
I am an AI nutrition system. I detected the following in this meal:
{items_json}

Total Estimated Calories: {total_cal} kcal.

Analyze this meal for realism. Consider:
1. Proportions: Does the mass of {item_name} make sense for its volume?
2. Redundancy: Are 'Pizza' and 'Dough' both detected? (Merge if so).
3. Composition: Is this a likely combination of foods?

Return a corrected JSON object with 'final_calories', 'final_macros', and 'logic'.
"""
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| YOLOv8 | Detection | ✓ | 8.4.31 | — |
| SAM 2 | Segmentation | ✓ | 5.4.0 | SAM 1 |
| GLPN | Depth | ✓ | 5.4.0 | — |
| Gemini API | LLM Validation | ✓ | — | Mock/Logic-only |
| OpenRouter | LLM Validation | ✓ | — | Gemini API |

**Missing dependencies with no fallback:**
- None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `pytest tests/test_multi_food.py` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MULTI-01 | YOLOv8 detects 3+ food items | Integration | `pytest tests/test_multi_food.py::test_yolo_detection` | ❌ Wave 0 |
| MULTI-02 | SAM 2 generates boxes for YOLO prompts | Unit | `pytest tests/test_multi_food.py::test_sam2_boxes` | ❌ Wave 0 |
| MULTI-03 | Prediction merger aggregates nutrients | Unit | `pytest tests/test_multi_food.py::test_merger_aggregation` | ❌ Wave 0 |
| MULTI-04 | LLM Validation corrects unrealistic input | Integration | `pytest tests/test_multi_food.py::test_llm_validation` | ❌ Wave 0 |
| MULTI-05 | `/predict-validated` returns JSON | E2E | `pytest tests/test_api.py::test_predict_validated` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `tests/test_multi_food.py` — New test suite for multi-food logic.
- [ ] `tests/data/complex_plate.jpg` — Multi-food sample image for testing.

## Sources

### Primary (HIGH confidence)
- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/models/yolov8/)
- [Meta SAM 2 GitHub](https://github.com/facebookresearch/sam2)
- [OpenRouter API Docs](https://openrouter.ai/docs)

### Secondary (MEDIUM confidence)
- [HuggingFace Food Detection Models](https://huggingface.co/models?search=yolov8+food)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Libraries are installed and verified.
- Architecture: HIGH - Box-prompting SAM 2 is the recommended SOTA pattern.
- Pitfalls: MEDIUM - Latency is the primary risk.

**Research date:** 2026-04-26
**Valid until:** 2026-05-26
