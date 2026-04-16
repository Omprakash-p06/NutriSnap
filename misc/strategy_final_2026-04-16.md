# NutriSnap: Final Strategic Architecture — 2026-04-16

**Status**: Definitive MVP blueprint. **10-dish accuracy-driven MVP.**  
Supersedes `misc/strategy_pivot_2026-04-16.md` and all prior architecture documents.

---

## Why 10 Dishes, Not Full Dataset

Proving high accuracy on a small, visually-distinct subset:
- dramatically reduces preprocessing time (hours → minutes)
- validates the core methodology before scaling
- avoids common failure modes (constant prediction, systematic bias) on a dataset too large to debug effectively
- once the 10-dish MVP hits targets (MAE ≤ 40 kcal), the same pipeline scales to 5k dishes with no architectural changes

---

## Phase 1 — Data Selection & Curation

### 1.1 MVP Dish Subset (10 Dishes)
Manually select 10 visually distinct dish types with enough variability in calorie density:

| # | Dish Type | Why |
|---|-----------|-----|
| 1 | Pizza | High fat/carb, circular shape |
| 2 | Salad | Low calorie, complex texture |
| 3 | Pasta | High carb, irregular portion |
| 4 | Rice Bowl | High carb, clear depth profile |
| 5 | Sandwich | Layered structure |
| 6 | Soup | Liquid depth, complex macros |
| 7 | Stir-fry | Mixed textures, variable portions |
| 8 | Omelette | High protein, flat |
| 9 | Smoothie | Liquid, uniform surface |
| 10 | Grilled Chicken Plate | High protein, clear segmentation |

Selection is done by `prepare_data.py --mvp-only` which uses heuristics from `component_weights.tsv` to identify dish types.

### 1.2 Ingredient-Mass Correction
For every dish in the 10-dish subset:
1. Open `component_weights.tsv` — each row is an ingredient and its gram weight
2. Sum all ingredient masses for the dish
3. Compare sum to the reported total dish mass
4. If `|sum - total| / total > 5%` → flag the sample (apply proportional correction or exclude)
5. Keep only dishes where the mass is within 5% of the reported total

**Effect**: 6–42% improvement in prediction metrics per published study on Nutrition5k.

### 1.3 Frame Filtering (from 360° Video)
For each dish, sample 1 frame per 5 from the 360° video (matching the original Nutrition5k paper protocol). Rank frames by:
- Focus sharpness (Laplacian variance)
- Lighting uniformity
- Minimal occlusion

Keep only the best-quality overhead frames per dish in the training set.

### 1.4 Official Data Split (by dish_id — no leakage)
- **Test set**: from official `dish_ids/splits/test_ids.txt` — locked, never used during training
- **Val set**: `GroupShuffleSplit` from remaining 85%, grouping by `dish_id`
- **Train set**: remaining 70%

All images of the same physical dish stay together in the same split. This is critical — each dish has multiple frames; mixing them across train/val = data leakage.

---

## Phase 2 — Advanced Preprocessing Pipeline

### 2.1 RGB
1. Resize → 224×224
2. ImageNet normalize: mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`

In code: Bilateral Filter (edge-preserving noise reduction) and CLAHE (contrast enhancement on L-channel in LAB space) are applied before normalization for better feature representation.

### 2.2 Depth
1. 16-bit → metres (÷ 10,000)
2. Median filter (3×3) — removes sensor noise
3. TELEA inpainting (OpenCV) — fills zero/missing pixels
4. Gaussian smoothing
5. Resize → 224×224, normalize to [0, 1]

### 2.3 SAM Segmentation with LoRA Fine-Tuning
1. Base: SAM ViT-B backbone
2. Add LoRA adapters to image encoder attention layers (low parameter count)
3. Fine-tune on Nutrition5k annotated food masks
4. Output: binary mask (food vs. background)
5. Apply mask to both RGB and depth: background pixels → 0

Generic SAM underperforms on food; LoRA provides food-specific accuracy with minimal extra parameters.

### 2.4 Data Augmentation (Online, post-masking, Albumentations)
Applied during training, not preprocessing — tensors saved without augmentation:
1. Random rotation ±30°
2. Horizontal flip (p=0.5)
3. Random crop/resize (scale 0.8–1.0)
4. Random brightness/contrast ±20%
5. Hue/saturation shift ±10°/±20°
6. Gaussian blur (kernel 3–5)
7. CoarseDropout (≤4 holes, ≤32×32px)

### 2.5 RGB-D Fusion with Channel-Spatial Attention
- RGB → EfficientNetV2-B0 → 1,280-dim appearance features
- Depth → DepthCNN → 64-dim geometric features
- Channel-spatial attention module fuses both
- Optional: concatenate ingredient embedding from `component_weights.tsv`

---

## Phase 3 — Three-Model Ensemble

| Model | Backbone | Input | Role |
|-------|----------|-------|------|
| **Primary** | EfficientNetV2-B0 | RGB 224×224 | Best accuracy/efficiency tradeoff |
| **Secondary** | ResNet101 | RGB 224×224 | Different inductive bias; ensemble diversity |
| **Tertiary** | Multi-Task CNN | RGB + Depth + ingredient embedding | RGB-D fusion with ingredient awareness |

### 3.1 5-Fold Stratified CV (by calorie bins)
1. Pool train + val dishes (70% + 15% = 85%)
2. Bin calorie values into 5 quantile groups (Very Low → Very High)
3. `StratifiedKFold(n_splits=5)` using calorie bins as strata, grouped by `dish_id`
4. For each fold: train on 4, validate on 1, save best checkpoint

### 3.2 Weighted Ensemble Inference
```
weight_i = 1 / MAE_i   (computed per fold on its validation set)
final_prediction = Σ (normalized_weight_i × pred_i)
```

---

## Phase 4 — Multi-Tier Verification Layer

### Tier 1: Rule-Based Validator (every prediction)
| Check | Criterion | Action |
|-------|-----------|--------|
| Hard bounds | cal 50–1500, prot 1–150, carb 1–250, fat 1–80 | Flag |
| Calorie consistency | `|cal – (4·prot + 4·carb + 9·fat)| > 20%` | Flag |
| Volume consistency | depth-derived volume < 50 cm³ or > 2000 cm³ | Flag |
| Ensemble uncertainty | std dev across 5 models > 50 kcal | Flag |

- All checks pass, std ≤ 50 kcal → **direct output** (< 200ms)
- Any flag → **Tier 2**

### Tier 2: Gemini 2.0 Flash API Fallback
1. **Prompt Step 1**: Identify food items, estimate nutritional content
2. **Prompt Step 2**: Compare with CV model predictions, ask "Are the CV values realistic? If not, provide corrected JSON."
3. Parse JSON → final output (1–3 seconds)

### Tier 3: USDA Database Cross-Reference (optional)
- Parse Gemini's identified food item
- Query USDA Food Data Central API
- Discrepancy > 20% → append caution note to user response

---

## Phase 5 — Training Configuration (RTX 3050 / 4GB)

| Parameter | Value |
|-----------|-------|
| Optimizer | AdamW |
| LR (heads, phase 1) | 1e-4 |
| LR (backbone partial, phase 2) | 1e-5 |
| LR (full backbone, phase 3) | 1e-6 |
| LR Schedule | Linear warmup (5 ep) → Cosine annealing |
| Loss | Huber loss |
| Dropout | 0.3 |
| Weight decay | 1e-5 |
| Batch size | 8 |
| Gradient accumulation | 4 steps → effective batch 32 |
| Mixed precision | AMP FP16 |
| Early stopping | Patience = 10 epochs |
| Max epochs | 100 |

### Transfer Learning Schedule
- **Epochs 1–10**: Backbone frozen, train regression heads only
- **Epochs 11–20**: Unfreeze last 3 backbone layers, LR 1e-5
- **Epochs 21+**: Full backbone unfrozen, LR 1e-6

---

## Phase 6 — Evaluation Targets

| Metric | Target |
|--------|--------|
| Calorie MAE | ≤ 40 kcal |
| Calorie MAPE | ≤ 12% |
| R² | ≥ 0.85 |
| RMSE | ≤ 60 kcal |
| Bias | ≈ 0 |
| Spearman correlation | ≥ 0.90 |
| Ensemble std dev | ≤ 50 kcal |
| Inference (normal) | < 200 ms |
| Inference (Gemini fallback) | 1–3 s |

**SOTA benchmark**: 14.9% PMAE (calories), 11.2% (mass) on Nutrition5k. MVP should match or beat this.

---

## Phase 7 — FastAPI Deployment

- `POST /predict` — accepts image, returns `image_id` immediately (non-blocking)
- `GET /result/{image_id}` — poll until ready; returns predictions + verification metadata

**User-facing output:**
- Calories, protein, carbs, fats
- Confidence: High / Medium / Low
- If Gemini used: *"This estimate was reviewed by a second-opinion AI."*

---

## MVP Success Checklist

- [ ] Data: 10-dish subset selected; ingredient-mass correction applied; frame filtering applied; dish_id-safe splits
- [ ] Preprocessing: RGB + depth pipelines; SAM-LoRA segmentation masks applied; augmentation active
- [ ] Models: Primary (EfficientNetV2-B0) + Secondary (ResNet101) + Tertiary (Multi-Task CNN + ingredients) trained
- [ ] Ensemble: 5-fold weighted ensemble inference implemented
- [ ] Verification: Rule validator + Gemini API fallback working
- [ ] Performance: Calorie MAE ≤ 40 kcal; inference < 200ms (normal path)
- [ ] API: FastAPI endpoints functional; single image → verified nutritional analysis

---

## Scaling Path (After MVP Validated)

Once MAE ≤ 40 kcal is confirmed on 10 dishes:
1. Expand `mvp_dish_count` in `data_config.yaml` → rerun `prepare_data.py`
2. Rerun `preprocess_full.py` for new dishes
3. Rerun `src/train.py` — same architecture, same pipeline, larger dataset

No architectural changes needed. The pipeline is designed to scale.

---

*See `misc/nutrisnap_pipeline_2026-04-16.svg` for the visual architecture diagram.*
