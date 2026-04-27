# NutriSnap 🍱

**AI-powered nutrition estimation from a single meal photo.**

NutriSnap is a production-oriented FastAPI backend that estimates **calories, protein, carbohydrates, and fats** from a single meal image using a three-stage, 3D-aware pipeline.

---

## 🏗️ Architecture Overview: The Three-Stage Pipeline

![Architecture Diagram](misc/nutrisnap_pipeline_2026-04-16.svg)

NutriSnap addresses the loss of 3D information in 2D photos by explicitly estimating volume before performing nutritional regression.

```
Image → [SAM 2 Segmentation] → [GLPN Depth Map] → [Composite Image] → [EfficientNetV2-B0] → [Isotonic Calibration] → [Results]
```

### 1. 🍽️ Segmentation (SAM 2)
The **Segment Anything Model 2 (SAM 2)** isolates the food item from background elements like plates, cutlery, and tables.

### 2. 📐 Depth Estimation (GLPN)
The **Global-Local Path Network (GLPN)** generates a depth map, recovering 3D structure and volume cues.

### 3. 🧠 Mass Regression (EfficientNetV2-B0)
An "enhanced composite" of the RGB image, mask, and depth map is fed into **EfficientNetV2-B0**. An explicit 3D volume scalar is fused into the regression head. The model predicts total mass using a log-transformed space and a **Correlation-Aware Loss** to ensure accurate ranking.

### 4. ⚖️ Post-Training Calibration
Finally, an **Isotonic Regression** calibrator corrects for scale bias, significantly boosting the R² and Spearman metrics.

---

## 🎯 Performance Results (MVP Subset - 20 Dishes)

### Supported MVP Dishes (20)
1. Breakfast Plate (scrambled eggs, turkey bacon, sausage, broccoli)
2. Caesar Salad
3. Bok Choy
4. Mediterranean Chicken & Grains
5. Fish & Caesar Salad with Eggplant
6. Fruit & Veggie Bowl
7. Broccoli Side
8. Pizza
9. Grains & Apple Salad
10. Brussels Sprouts, Celery & Olives
11. Mixed Pork & Fish Grain Bowl
12. Brussels Sprouts, Celery & Olives (variant)
13. Brussels Sprouts, Celery & Olives (variant)
14. Brussels Sprouts, Celery & Olives (variant)
15. Celery Side
16. Raspberries
17. Brussels Sprouts Side
18. Empty Plate (Calibration sample)
19. Olives Side
20. Breakfast Bowl (eggs, bacon, broccoli, strawberries, raspberries)

| Metric | Target | **Achieved (Calibrated)** | Status |
|---|---|---|---|
| Mass MAE | ≤ 50 g | **46.22 g** | ✅ |
| R² Score | > 0.40 | **0.4314** | ✅ |
| Spearman ρ | > 0.50 | **0.6047** | ✅ |
| Calorie MAE (est) | ≤ 40 kcal | **~35 kcal** | ✅ |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- CUDA 11.8+ (GTX 1650 or better)
- 4 GB VRAM minimum

### Installation
```powershell
git clone https://github.com/Omprakash-p06/NutriSnap.git
cd NutriSnap
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
NutriSnap/
├── src/nutrisnap/
│   ├── pipeline/           # SAM 2 and GLPN orchestration
│   ├── models/             # EfficientNet regression heads
│   ├── data/               # Preprocessing & mass correction
│   └── api/                # FastAPI server
├── scripts/                # Training and evaluation scripts
├── configs/                # Pipeline and model configurations
└── misc/
    └── strategy_final.md   # ← Definitive implementation guide
```

---

## 📄 License
MIT — see [LICENSE](LICENSE).
