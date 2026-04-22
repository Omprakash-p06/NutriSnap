# Project Overview: NutriSnap

This plan moves beyond the proof-of-concept phase and outlines a path toward a production-grade system. The core enhancements are:

*   **Hardware Optimized for GTX 1650 4GB:** We'll use gradient accumulation, mixed precision, and a carefully selected model architecture to stay within your VRAM limits.
*   **Narrow, Accurate Focus (Minimum Viable Product):** Training on **5-10 hand-picked dish types** (e.g., pizza, salad, pasta) ensures high accuracy and provides a strong foundation.
*   **Multi-Stage Computer Vision Pipeline:** This is not just a CNN. The plan details a robust pipeline for depth processing, a hybrid volume estimation method for concave shapes, and a fine-tuned segmentation model.

Below is a high-level overview of the entire system architecture, showing how each component connects:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NUTRISNAP SYSTEM ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA SPLITTING                                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│ │ Raw Dataset │───▶│  Clean      │───▶│  Train/Val  │───▶│ Official Test Split │ │
│ │ (Nutrition5k)│    │  Subset     │    │   Splits    │    │ (dish_ids/splits)   │ │
│ └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: PREPROCESSING & CV TECHNIQUES                                           │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│ │ RGB Pipeline│    │Depth Pipeline│   │Segmentation │    │ Volume Estimation   │ │
│ │ - Noise     │    │- Cleaning   │    │(MealSAM)    │    │ - Convex Hull       │ │
│ │   Reduction │    │- Inpainting │    │- Masking    │    │ - Alpha Shape       │ │
│ │ - CLAHE     │    │- Smoothing  │    │             │    │ - Hybrid Selection  │ │
│ └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: MODEL ARCHITECTURE                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────────┐  │
│ │                      Multi-Task Regression Model                             │  │
│ │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │  │
│ │  │    Backbone     │  │  Scalar Inputs  │  │     Regression Heads        │  │  │
│ │  │ EfficientNetV2  │  │ - Log Volume    │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│  │
│ │  │      +          │  │ - Pixel Area    │  │  │Cals │ │Prot │ │Carbs│ │Fats ││  │
│ │  │ Swin Transformer│  │ - Food Embedding│  │  └─────┘ └─────┘ └─────┘ └─────┘│  │
│ │  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │  │
│ └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: TRAINING STRATEGY                                                       │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│ │5-Fold CV    │───▶│Ensemble     │───▶│Uncertainty  │───▶│Mixed Precision      │ │
│ │(dish-level) │    │of 5 Models  │    │Weighted Loss│    │+ Gradient Accum.    │ │
│ └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5-6: EVALUATION & POST-PROCESSING                                          │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────────────┐│
│ │Evaluation   │───▶│Rule-Based   │───▶│API Fallback (Gemini/Grok) - Optional   ││
│ │Metrics      │    │Validator    │    │Triggered on low confidence/rule failure ││
│ └─────────────┘    └─────────────┘    └─────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: BACKEND INTEGRATION (FastAPI)                                           │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│ │ /predict    │───▶│Background   │───▶│ /result     │───▶│ Response with       │ │
│ │ Endpoint    │    │Tasks        │    │ Endpoint    │    │ Predictions +       │ │
│ │             │    │             │    │             │    │ Verification Status │ │
│ └─────────────┘    └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Phase 1: Data Splitting

The goal is to create robust, leak‑proof splits.

1.  **Audit Raw Data**
    *   **Action:** Verify that the dataset is correctly stored in `datasets/raw`. Run a basic script to count the number of unique `dish_id`s and check for file corruption.
    *   **Reference:** The official dataset includes a custom scanning rig with overhead and side-angle images.

2.  **Use Official Train/Test Splits**
    *   **Action:** The Nutrition5k repository provides official split `dish_id`s in the `dish_ids/splits/` directory. Use these to create your `test_dish_ids.txt` and `train_dish_ids.txt`.
    *   **Critical Rule:** All incremental scans that compose a unique plate are held within the same split to avoid overlap between the train and test sets.

3.  **Create Subset of Dish Types**
    *   **Action:** From the official `train_dish_ids`, manually select **5-10 dish types** (e.g., `dish_1698765432` for pizza). Create a mapping file `selected_dishes.json`. For a Minimum Viable Product (MVP), focus on a few distinct types before scaling up.

4.  **Create Validation Split**
    *   **Action:** From your selected training dishes, use a `GroupShuffleSplit` (grouping by `dish_id`) to allocate 15% as a validation set. Save these IDs to `val_dish_ids.txt`.

5.  **Create 5 Folds for Cross-Validation**
    *   **Action:** Implement `StratifiedGroupKFold` with `n_splits=5`. Use calorie bins for stratification and group by `dish_id`. Store the fold indices in `cv_folds.json`.

## Phase 2: Preprocessing & CV Techniques

The system's accuracy depends heavily on the quality of the preprocessing steps. A robust pipeline is crucial for handling the inherent noise in RGB-D data and for accurately isolating the food item.

### 2.1 RGB Image Preprocessing Pipeline

*   **Noise Reduction:** Apply a **bilateral filter** to reduce noise while preserving food texture edges.
*   **Contrast Enhancement:** Apply **CLAHE (Contrast Limited Adaptive Histogram Equalization)** to the L-channel of the LAB color space to improve local contrast and make food features more distinct.
*   **Resizing & Normalization:** Resize the image to **224x224** pixels. Normalize using **ImageNet mean and standard deviation** (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]).

### 2.2 Depth Map Preprocessing Pipeline

*   **Unit Conversion:** Convert raw depth values from 16-bit to meters. The typical reliable range is **0 to 0.4 meters**.
*   **Noise Cleaning Pipeline:** Implement a sequential process: **Median filter** → **Outlier removal** (flag and cap values outside the reliable range) → **Morphological closing** to fill small holes.
*   **Inpainting:** Use the **TELEA inpainting algorithm** (available in OpenCV as `cv2.inpaint`) to repair missing or zero-value depth pixels, using neighboring depth values.
*   **Smoothing:** Apply a **Gaussian filter** to reduce high-frequency noise.
*   **Normalization & Resizing:** Normalize the depth map to the range [0, 1] and resize it to 224x224 to match the RGB image dimensions.

### 2.3 Segmentation & Masking (with Fine-Tuned SAM)

*   **Base Model:** Use **SAM (Segment Anything Model)** for initial segmentation.
*   **Fine-Tuning (Crucial):** Zero‑shot SAM underperforms for food images. You must fine‑tune it. A specialized food segmentation model, **MealSAM**, with a ViT-B backbone, is available for this purpose.
*   **Data for Fine-Tuning:** Use the manually annotated segmentation labels for 3,224 images from the Nutrition5k dataset to fine-tune the model.
*   **Implementation:** Apply the fine-tuned model to generate a binary food mask and apply it to both RGB and depth images to zero out the background, isolating the food item.

### 2.4 Hybrid Volume Estimation

*   **Method 1: Convex Hull:** Use this for generally convex food shapes. It calculates the volume of the smallest convex polygon that encloses the point cloud.
*   **Method 2: Alpha Shape:** Use this for concave shapes, like a bowl of pasta. It creates a tighter-fitting mesh around the point cloud.
*   **Hybrid Selection Logic:** Implement a lightweight classifier (e.g., based on point cloud curvature) to determine if the shape is convex or concave, and then select the appropriate method (Convex Hull for convex, Alpha Shape for concave). Research has evaluated these methods, showing their complementary strengths and error rates.
*   **Output:** Store **log volume (cm³)** and **2D pixel area** as scalar features for each sample.

### 2.5 Data Augmentation (Applied Online)

*   **Augmentation Pipeline (Albumentations):**
    *   **Geometric:** Random rotation (±30°), horizontal flip, random crop/resize (scale 0.8–1.0).
    *   **Color:** Random brightness and contrast (±20%), hue/saturation shift (±10°/±20%).
    *   **Blur & Noise:** Gaussian blur (kernel 3–5), additive Gaussian noise.
    *   **Occlusion:** Coarse dropout (up to 4 holes, size up to 32x32 pixels) to simulate real-world occlusions like utensils.
*   **Important:** Apply augmentation **after** the food mask is applied, not before.

## Phase 3: Model Architecture

The choice of model directly impacts accuracy and hardware compatibility.

1.  **Backbone (Hybrid Approach):**
    *   **Primary:** Use **EfficientNetV2-B0** as the main backbone for efficient feature extraction. It's lightweight (5.3 million parameters) and well-suited for your hardware constraints.
    *   **Enhancement (Optional for MVP, Recommended for Production):** Integrate a **Swin Transformer** branch to capture long-range dependencies and global context. Research shows that combining EfficientNet for feature extraction and Swin Transformer for capturing long-range dependencies significantly improves accuracy for food nutrient recognition.

2.  **Scalar Inputs:** Concatenate the following features with the backbone's output:
    *   **log(volume)** from Phase 2.4.
    *   **2D pixel area** from Phase 2.4.
    *   **Food category embedding** (from a small, separate classification head).

3.  **Multi-Task Regression Heads:**
    *   Design separate small MLP heads for each nutrient: calories, protein, carbs, fats.
    *   **Output Activation:** Use **linear activation** (no sigmoid), but consider predicting the **log of the value** and exponentiating the output. This often stabilizes training.

4.  **GPU Memory Optimization (Critical for GTX 1650 4GB):**
    *   **Batch Size:** Set batch size to 8.
    *   **Gradient Accumulation:** Simulate a larger batch of 32 by accumulating gradients over 4 steps.
    *   **Mixed Precision (FP16) Training:** Use PyTorch's automatic mixed precision to reduce memory usage and speed up training.

## Phase 4: Training Strategy

1.  **5-Fold Cross-Validation Ensemble:**
    *   Train **5 independent models** using the folds created in Phase 1. For each fold:
    *   **Transfer Learning Schedule:**
        *   Freeze the backbone for the first 10 epochs; train only the regression heads.
        *   Unfreeze the backbone and fine-tune with a lower learning rate (e.g., 1e-5).
    *   **Optimizer:** AdamW (1e-4 for heads, 1e-5 for backbone).
    *   **Loss Function:** Use an **Uncertainty Weighted Loss** to automatically balance the contribution of each nutrient regression task.
    *   **Scheduler:** Linear warmup over 5 epochs, then cosine annealing.
    *   **Early Stopping:** Stop training if validation loss does not improve for 10 epochs.
    *   **Regularization:** Use dropout (p=0.3), weight decay (L2), and label smoothing.

2.  **Ensemble Inference:**
    *   For a given input, run all 5 models and aggregate their predictions using the **median**. The median is more robust to outliers than the mean.

## Phase 5: Evaluation Metrics

Do not rely on MAE alone. Use a suite of metrics to get a comprehensive view of model performance.

| Metric | Target | Purpose & How to Calculate |
| :--- | :--- | :--- |
| **Calorie MAE** | ≤ 45 kcal | Measures average absolute error. Compare against the 40.05 kcal MAE reported in recent research. |
| **Calorie MAPE** | ≤ 20% | Measures average percentage error. The state-of-the-art on Nutrition5k is 14.72%. |
| **R² Score** | ≥ 0.85 | Indicates how well the model explains the variance in the data. |
| **Std Dev of Predictions** | > 0 | **Crucial for detecting constant predictions.** Measures diversity across the 5 ensemble models. |
| **Spearman Correlation** | ≥ 0.9 | Measures rank-order correlation; not fooled by systematic scale errors. |
| **Bias** | Near 0 | Measures systematic over- or under-prediction. `bias = mean(predicted - true)`. |

## Phase 6: Post-Processing & Verification Layer

This ensures that the final output is realistic and safe for users.

1.  **Rule-Based Validator:**
    *   **Hard Bounds:** Calorie range: 50–1500 kcal; Protein: 1–150g; Carbs: 1–250g; Fats: 1–80g.
    *   **Consistency Check:** Ensure the calorie prediction is within a 20% margin of the energy calculated from the predicted macronutrients (`calories >= 4*protein + 4*carbs + 9*fats * 0.8`).

2.  **API Fallback (Gemini/Grok - Optional, for validation):**
    *   **Trigger:** Activate the API call only when the rule validator flags an issue OR when the ensemble variance is high (e.g., std dev > 50 kcal).
    *   **Purpose:** Use the API as a lightweight **consistency check** or "second opinion," not as the primary estimator. You can select and integrate the API key later in the project.
    *   **Prompt Structure:** "A computer vision model predicted [CV prediction] for this food image. Are these values realistic for the visible portion? If not, provide a corrected estimate."

## Phase 7: Backend Integration (FastAPI)

This outlines the API endpoints for a production-ready system.

*   **`/predict` (POST) Endpoint:** Accepts an image file. Returns a `202 Accepted` status and an `image_id` immediately. Offloads the heavy model inference to a `BackgroundTask` to prevent server blocking.
*   **`/result/{image_id}` (GET) Endpoint:** Used to poll for the completed prediction. Returns a `202 Processing` status if the result is not ready, or the final prediction with its verification status once it is.

## Final Summary Table

| Phase | Key Actions | Critical Dependencies |
| :--- | :--- | :--- |
| **1: Data Splitting** | Use official dish_id splits; GroupShuffleSplit for val; StratifiedGroupKFold for 5-fold. | `dish_ids/splits/` directory from Nutrition5k. |
| **2: Preprocessing** | RGB: bilateral filter + CLAHE. Depth: TELEA inpainting + smoothing. Segmentation: fine-tuned MealSAM. Volume: hybrid Convex Hull/Alpha Shape. | `opencv`, `albumentations`, fine-tuned SAM weights. |
| **3: Architecture** | EfficientNetV2-B0 + (optional) Swin Transformer branch. Multi-task heads. | `timm` library, ImageNet weights. |
| **4: Training** | 5-fold CV, ensemble, mixed precision, gradient accumulation. | `pytorch-lightning`, GPU with 4GB VRAM. |
| **5: Evaluation** | MAE, MAPE, R², Std Dev, Spearman, Bias. | `scikit-learn` metrics. |
| **6: Post-Processing** | Rule-based validator + API fallback (Gemini/Grok). | API keys (optional). |
| **7: Backend** | FastAPI with `/predict` and `/result` endpoints. | `fastapi`, `uvicorn`. |
