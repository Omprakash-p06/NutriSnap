# **Software Requirements Specification (SRS)**

## **Project: NutriSnap AI: Ingredient-Aware Multi-Food Detection and Nutrition Estimation**

**Version:** 2.1  
**Status:** Final Draft  
**Date:** February 09, 2026

---

## **0. Document Control**

### **0.1 Team Members**

| Name | USN | Role |
| :---- | :---- | :---- |
| **Vishwajith Chakravarthy** | 1MS23IS150 | Frontend Developer / UI/UX |
| **Vittal Gangappa Bhajantri** | 1MS23IS151 | Backend Engineer / DevOps |
| **Omprakash Panda** | 1MS24IS411 | Lead Developer / AI Architect |
| **Sindhu B L** | 1MS24IS413 | Data Engineer / QA |

### **0.2 Revision History**

| Version | Date | Author | Changes |
| :---- | :---- | :---- | :---- |
| 1.0 | Jan 2026 | Team | Initial draft |
| 1.4 | Feb 05, 2026 | Omprakash | Added AI model specifications |
| 2.0 | Feb 09, 2026 | Omprakash | Added project file structure, refined architecture |
| 2.1 | Feb 09, 2026 | Omprakash | Added detailed scope, constraints, deployment strategy |

---

## **Table of Contents**

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Project File Structure](#3-project-file-structure)
4. [AI Model Specifications](#4-ai-model-specifications)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [External Interface Requirements](#7-external-interface-requirements)
8. [Database Schema](#8-database-schema)
9. [Development Standards](#9-development-standards)
10. [Deployment Strategy](#10-deployment-strategy)
11. [Appendices](#11-appendices)

---

## **1. Introduction**

### **1.1 Purpose**

This Software Requirements Specification (SRS) document provides a complete description of **NutriSnap AI**, an automated nutrition tracking system that uses computer vision and multi-agent AI to detect food items from images, estimate portion sizes, and calculate nutritional values. This document is intended for:
- Development team members
- Project guide and evaluators
- Future maintainers and contributors

### **1.2 Scope**

**Product Name:** NutriSnap AI: Ingredient-Aware Multi-Food Detection and Nutrition Estimation

#### **1.2.1 Current Scope (Version 1.0 - Mini Project Implementation)**

The system will deliver the following capabilities:
- **Multi-food detection** from a single image for 4 specific Indian food items (Rice, Dal, Paneer, Roti)
- **Portion estimation** with target accuracy of ≤20% Mean Absolute Percentage Error (MAPE)
- **Nutrition calculation** for calories, protein, carbohydrates, and fat
- **Meal logging and tracking** with simple historical view
- **Web-based interface** accessible from PC and mobile browsers
- **Multi-agent architecture** using open-source frameworks for modularity and scalability

#### **1.2.2 Image Input Methods**
- Upload pre-existing images (downloaded from Google, saved photos)
- Capture directly via webcam (PC)
- Capture via phone camera through web browser (when hosted)

#### **1.2.3 Deployment Modes**
- **Local development:** Runs on PC with NVIDIA GPU (RTX 3050 or equivalent)
- **Production deployment:** Dockerized web application hosted on cloud platforms (Render/Railway/Vercel/Netlify)

#### **1.2.4 Out of Scope (Future Roadmap)**
- Ingredient recognition beyond 4 core items (40+ foods planned in v2)
- Full personalized meal planning engine
- AI chatbot assistant
- Recipe generation
- Native mobile applications (iOS/Android)
- Multi-cuisine expansion beyond Indian staples

### **1.3 Core Features Overview**

| # | Feature | Description | v1 Status |
| :---- | :---- | :---- | :---- |
| 1 | **Multi-Food Detection** | Detect Rice, Dal, Paneer, Roti from single photo | ✅ Implemented |
| 2 | **Portion Estimation** | Estimate weight in grams using visual features | ✅ Implemented |
| 3 | **Nutrition Calculation** | Calculate calories & macros per item | ✅ Implemented |
| 4 | **Meal Logging** | Save meals with timestamp & nutrition | ✅ Implemented |
| 5 | **Simple Dashboard** | Daily calories, weekly trend | ✅ Implemented |
| 6 | **User Correction** | Manual adjustment of portions | ✅ Implemented |
| 7 | **Ingredient-Level Recognition** | Identify components within dishes | ❌ v2 |
| 8 | **Personalized Meal Planning** | Custom daily/weekly meal plans | ❌ v2 |
| 9 | **AI Nutrition Chatbot** | Answer nutrition queries | ❌ v2 |
| 10 | **AI Recipe Generator** | Generate recipes based on ingredients | ❌ v2 |

### **1.4 Definitions and Acronyms**

| Term | Definition |
| :---- | :---- |
| **SRS** | Software Requirements Specification |
| **MVP** | Minimum Viable Product |
| **TDEE** | Total Daily Energy Expenditure |
| **BMI** | Body Mass Index |
| **MAPE** | Mean Absolute Percentage Error |
| **CLAHE** | Contrast Limited Adaptive Histogram Equalization |
| **DIP** | Digital Image Processing |
| **CV** | Computer Vision |
| **Agent** | Self-contained software module for a specific inference task |
| **YOLO** | You Only Look Once (Object Detection Architecture) |
| **VLM** | Vision Language Model (e.g., LLaVA) |
| **LLM** | Large Language Model (e.g., Llama, Gemma) |
| **RAG** | Retrieval-Augmented Generation |
| **CrewAI** | Multi-agent orchestration framework |

### **1.5 References**

**Standards & Guides**
- IEEE Std 830-1998: IEEE Recommended Practice for SRS
- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html

**AI Models**
- Ultralytics YOLO: https://docs.ultralytics.com/
- Depth Anything V2: https://github.com/DepthAnything/Depth-Anything-V2
- Segment Anything Model (SAM): https://github.com/facebookresearch/segment-anything
- LLaVA: https://llava-vl.github.io/

**Datasets**
- Khana Dataset (Indian Food): https://www.kaggle.com/datasets/omkarprabhu99/indian-food-classification
- FoodSeg103 Benchmark: https://github.com/LARC-CMU-SMU/FoodSeg103-Benchmark-v1
- USDA FoodData Central: https://fdc.nal.usda.gov/

**Frameworks**
- CrewAI: https://docs.crewai.com/
- FastAPI: https://fastapi.tiangolo.com/

---

## **2. Overall Description**

### **2.1 Product Perspective**

NutriSnap AI is a standalone web application that combines:
- **Computer Vision** for automated food recognition
- **Machine Learning** for portion size estimation
- **Multi-Agent Systems** for modular task orchestration
- **Web Technologies** for universal accessibility

| Layer | Technology | Purpose |
| :---- | :---- | :---- |
| **Frontend** | React + TailwindCSS + Recharts | User interface & data visualization |
| **Backend** | FastAPI (Python) | REST API & orchestration layer |
| **AI Orchestration** | CrewAI | Multi-agent coordination |
| **Database** | SQLite (dev) / PostgreSQL (prod) | User profiles, meal logs |
| **AI Models** | YOLOv8-Nano + XGBoost | Detection, portion estimation |

### **2.2 System Architecture**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENT SIDE                                │
│                     (Image Upload / Capture)                            │
│                         Desktop / Mobile                                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       API & ORCHESTRATION LAYER                         │
│                          FastAPI Backend                                │
│                               │                                         │
│                    ┌──────────▼──────────┐                              │
│                    │  Coordinator Agent  │                              │
│                    │      (CrewAI)       │                              │
│                    └──────────┬──────────┘                              │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   Detection   │      │    Portion    │      │   Nutrition   │
│     Agent     │      │     Agent     │      │     Agent     │
│ (YOLOv8-Nano) │      │   (XGBoost)   │      │   (Lookup)    │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌───────────────────┐
                    │   JSON Response   │
                    │  (Meal Nutrition) │
                    └───────────────────┘
```

### **2.3 User Classes and Characteristics**

| User Type | Description | Technical Skill | Primary Use Case |
| :---- | :---- | :---- | :---- |
| **Health-Conscious User** | College students, fitness enthusiasts | Basic | Quick calorie tracking |
| **Medical Users** | Dietary restrictions (diabetes) | Basic | Strict monitoring |
| **Developer/Admin** | Team members maintaining system | Advanced | Updates, model retraining |

### **2.4 Operating Environment**

#### **2.4.1 Development Environment**
| Component | Specification |
| :---- | :---- |
| **OS** | Windows 11 / Ubuntu 22.04 / macOS |
| **CPU** | Intel Core i5 (8th gen+) or AMD Ryzen 5 |
| **RAM** | 16GB DDR4 minimum |
| **GPU** | NVIDIA RTX 3050 (4GB VRAM) or better |
| **Storage** | 256GB SSD |
| **Python** | 3.10+ |
| **Docker** | Docker Desktop |

#### **2.4.2 Production Environment**
| Component | Specification |
| :---- | :---- |
| **Backend Hosting** | Render / Railway / Hugging Face Spaces (Docker) |
| **Frontend Hosting** | Vercel / Netlify (static) |
| **Container Memory** | 512MB - 2GB RAM |

#### **2.4.3 Browser Compatibility**
| Browser | Version | Support |
| :---- | :---- | :---- |
| Chrome | 100+ | ✅ Full |
| Firefox | 100+ | ✅ Full |
| Safari | 15+ | ✅ Full |
| Edge | 100+ | ✅ Full |
| Mobile Chrome/Safari | Latest | ✅ Full (camera support) |

### **2.5 Design and Implementation Constraints**

#### **2.5.1 Technical Constraints**
| Constraint | Requirement |
| :---- | :---- |
| **No Proprietary APIs** | No paid AI services (OpenAI, Google Gemini) for core functionality |
| **Model Size** | Total model weights < 100MB for efficient deployment |
| **Memory Footprint** | Docker container must run within 2GB RAM |
| **Inference Speed** | End-to-end processing < 3 seconds on target hardware |

#### **2.5.2 Data Privacy Constraints**
- All image analysis happens server-side within deployed instance
- No user images sent to external third-party services
- User data stored only with explicit consent

#### **2.5.3 Academic Constraints**
- All dependencies must use permissive licenses (MIT, Apache 2.0, BSD)
- Custom training and integration work must be clearly documented
- Datasets must have academic/research-friendly licenses

### **2.6 Assumptions and Dependencies**

#### **2.6.1 Assumptions**
- Users have stable internet connection for web access
- Images are reasonably well-lit and in-focus
- Food items are visible and not heavily occluded
- Users understand basic nutrition concepts (calories, macros)

#### **2.6.2 Dependencies**
| Dependency | Type | Risk |
| :---- | :---- | :---- |
| Khana Dataset | Data | Low - publicly available |
| CrewAI Framework | Library | Low - MIT license, active development |
| YOLOv8 | Model | Low - widely used, stable |
| Free-tier hosting | Infrastructure | Medium - may have rate limits |

---

## **3. Project File Structure**

```
NutriSnap/
│
├── README.md                          # Project overview and setup
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Production container
├── docker-compose.yml                 # Local development setup
├── .gitignore                         # Git ignore rules
│
├── backend/                           # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # Configuration settings
│   │
│   ├── routes/                        # API Routes
│   │   ├── __init__.py
│   │   ├── food.py                    # Food detection & nutrition
│   │   ├── meals.py                   # Meal logging
│   │   ├── dashboard.py               # Dashboard data
│   │   └── health.py                  # Health check endpoint
│   │
│   ├── schemas/                       # Pydantic Models
│   │   ├── __init__.py
│   │   ├── food.py                    # Food detection schemas
│   │   ├── meal.py                    # Meal schemas
│   │   └── nutrition.py               # Nutrition schemas
│   │
│   ├── models/                        # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── user.py                    # User model
│   │   ├── meal.py                    # Meal model
│   │   └── food_item.py               # Food item model
│   │
│   ├── services/                      # Business Logic
│   │   ├── __init__.py
│   │   ├── preprocessing.py           # Image preprocessing pipeline
│   │   ├── nutrition_service.py       # Nutrition lookup
│   │   └── metrics.py                 # BMI, TDEE calculations
│   │
│   └── database.py                    # Database connection
│
├── ai_engine/                         # AI Processing Engine (CrewAI)
│   ├── __init__.py
│   ├── coordinator.py                 # CrewAI Coordinator Agent
│   │
│   ├── agents/                        # Specialized AI Agents
│   │   ├── __init__.py
│   │   ├── detection_agent.py         # YOLOv8 food detection
│   │   ├── portion_agent.py           # XGBoost portion estimation
│   │   └── nutrition_agent.py         # Nutrition lookup
│   │
│   ├── models/                        # AI Model Wrappers
│   │   ├── __init__.py
│   │   ├── yolo_model.py              # YOLOv8 wrapper
│   │   ├── portion_model.py           # XGBoost wrapper
│   │   ├── depth_model.py             # Depth Anything V2
│   │   └── segmentation_model.py      # SAM wrapper
│   │
│   ├── tools/                         # CrewAI Tools
│   │   ├── __init__.py
│   │   ├── image_tool.py              # Image preprocessing
│   │   └── nutrition_lookup_tool.py   # Database lookup
│   │
│   └── config/                        # AI Configuration
│       ├── __init__.py
│       └── model_config.py            # Model paths, thresholds
│
├── ml/                                # Machine Learning
│   ├── train_yolo.py                  # YOLOv8 fine-tuning
│   ├── train_portion.py               # Portion model training
│   ├── train_depth.py                 # Depth model training
│   ├── preprocess.py                  # Image preprocessing & augmentation
│   ├── data_exploration.py            # Dataset analysis
│   ├── evaluate.py                    # Model evaluation
│   │
│   ├── data/                          # Training Data (git-ignored)
│   │   ├── raw/
│   │   ├── processed/
│   │   └── annotations/
│   │
│   └── weights/                       # Model Weights (git-ignored)
│       ├── yolov8_food.pt
│       └── portion_model.joblib
│
├── frontend/                          # React Frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   ├── public/
│   │   └── assets/
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       │
│       ├── api/                       # API Client
│       │   ├── client.js
│       │   ├── food.js
│       │   └── meals.js
│       │
│       ├── components/                # React Components
│       │   ├── common/
│       │   │   ├── Button.jsx
│       │   │   ├── Card.jsx
│       │   │   ├── Loader.jsx
│       │   │   └── Navbar.jsx
│       │   │
│       │   ├── food/
│       │   │   ├── CameraCapture.jsx
│       │   │   ├── FoodResults.jsx
│       │   │   ├── NutritionCard.jsx
│       │   │   └── PortionSlider.jsx
│       │   │
│       │   └── dashboard/
│       │       ├── CalorieGauge.jsx
│       │       ├── MacroChart.jsx
│       │       └── MealHistory.jsx
│       │
│       ├── pages/
│       │   ├── Home.jsx
│       │   ├── Scan.jsx
│       │   ├── History.jsx
│       │   └── Profile.jsx
│       │
│       ├── hooks/
│       │   ├── useCamera.js
│       │   └── useNutrition.js
│       │
│       └── utils/
│           └── formatters.js
│
├── data/                              # Data Assets
│   ├── nutrition_db/
│   │   ├── nutrition.json
│   │   └── food_mappings.json
│   │
│   └── class_labels/
│       └── food_classes.yaml
│
├── configs/                           # Configuration Files
│   ├── yolo_train.yaml
│   └── portion_model.yaml
│
└── scripts/
    ├── setup_db.py
    └── download_models.py
```

---

## **4. AI Model Specifications**

### **4.1 Detection Agent (YOLOv8-Nano)**

| Attribute | Specification |
| :---- | :---- |
| **Model** | Ultralytics YOLOv8-Nano (yolov8n.pt base) |
| **Task** | Multi-class food object detection |
| **Classes** | 4 items: Rice, Dal, Paneer, Roti |
| **Input** | RGB Image (640×640 recommended) |
| **Output** | Bounding boxes, class IDs, confidence scores |
| **Model Size** | ~6MB (.pt file) |
| **Parameters** | ~3 million |
| **Inference Speed** | ~1-2ms (GPU), ~50-100ms (CPU) |
| **Framework** | PyTorch / Ultralytics |

**Why YOLOv8-Nano:**
- **Small dataset suitability:** Nano models generalize better on 300-500 images
- **Resource efficiency:** Fits in Docker container with other components
- **Sufficient capacity:** 4-class problem is simple; achieves 85-90% mAP
- **Fast inference:** Real-time performance even on free-tier CPU hosting

### **4.2 Portion Agent (XGBoost)**

| Attribute | Specification |
| :---- | :---- |
| **Model** | XGBoost Regressor |
| **Task** | Portion size estimation (grams) |
| **Features** | Bounding box area, aspect ratio, relative size |
| **Output** | Estimated weight in grams |
| **Model Size** | < 1MB each |
| **Training Time** | < 1 minute per class on CPU |
| **Framework** | Scikit-learn / XGBoost |

**Per-Class Models:**
| Food | Small | Medium | Large |
| :---- | :---- | :---- | :---- |
| Rice | 100g | 150g | 200g |
| Dal | 150g | 200g | 250g |
| Paneer | 50g | 80g | 120g |
| Roti | 30g | 40g | 50g |

### **4.3 Nutrition Agent**

| Attribute | Specification |
| :---- | :---- |
| **Task** | Nutrition data lookup & calculation |
| **Sources** | USDA FoodData Central, Local JSON |
| **Output** | Calories, Protein, Carbs, Fats per item |

**Nutrition Database (per 100g):**
| Food | Calories | Protein | Carbs | Fat |
| :---- | :---- | :---- | :---- | :---- |
| Rice | 130 | 2.7g | 28.2g | 0.3g |
| Dal | 130 | 7.5g | 15.0g | 6.0g |
| Paneer | 265 | 18.3g | 1.2g | 20.8g |
| Roti | 297 | 11.0g | 51.0g | 5.8g |

### **4.4 Depth & Segmentation Modules**

| Module | Model | Purpose |
| :---- | :---- | :---- |
| **Depth Estimation** | Depth Anything V2 | Volumetric portion estimation |
| **Segmentation** | SAM (Segment Anything) | Precise food boundaries |

### **4.5 Image Preprocessing Pipeline**

All images undergo the following Digital Image Processing (DIP) steps before training and inference:

**Stage 1: Basic Preprocessing**

| Step | Technique | Description |
| :---- | :---- | :---- |
| 1 | **Resizing** | Resize to 640×640 pixels (YOLO input size) |
| 2 | **Normalization** | Scale pixel values to [0, 1] range |
| 3 | **Color Space Conversion** | Convert BGR to RGB for model compatibility |

**Stage 2: Image Enhancement**

| Step | Technique | Description |
| :---- | :---- | :---- |
| 4 | **Noise Reduction** | Gaussian/Median blur for noisy images |
| 5 | **Histogram Equalization** | CLAHE for contrast enhancement in low-light |
| 6 | **White Balance** | Gray-world algorithm for color correction |
| 7 | **Sharpening** | Unsharp masking to enhance food edges |
| 8 | **Gamma Correction** | Adjust exposure for over/underexposed images |

**Stage 3: Segmentation & Masking**

| Step | Technique | Description |
| :---- | :---- | :---- |
| 9 | **Background Removal** | SAM-based segmentation to isolate food |
| 10 | **Food Region Masking** | Create binary masks for individual items |
| 11 | **Edge Detection** | Canny/Sobel operators for boundary refinement |
| 12 | **ROI Extraction** | Crop regions of interest for focused training |
| 13 | **Contour Detection** | Identify food item boundaries for annotation |

**Stage 4: Data Augmentation (Training Only)**

| Augmentation | Purpose |
| :---- | :---- |
| **Random Rotation** (±15°) | Handle varied plate orientations |
| **Horizontal Flip** | Increase dataset diversity |
| **Brightness/Contrast** | Simulate different lighting conditions |
| **Random Crop & Zoom** | Focus on different food regions |
| **Mosaic Augmentation** | YOLO-specific multi-image training |
| **Color Jitter** | Vary hue, saturation for robustness |
| **Cutout/Mixup** | Regularization for better generalization |

**Benefits:**
- **Faster Training:** Clean, normalized images reduce model convergence time
- **Better Accuracy:** Segmentation isolates food items, reducing background noise
- **Robust Detection:** Augmentation ensures model generalizes to real-world conditions

### **4.6 Preprocessing Implementation Details**

The actual preprocessing pipeline implemented in `ml/preprocess.py` uses OpenCV:

#### **Step 1: Resize (Geometric Transformation)**
```python
cv2.resize(image, (640, 640), interpolation=cv2.INTER_LINEAR)
```
- Converts all images to **640×640 pixels** (YOLO input size)
- Uses **bilinear interpolation** for smooth scaling

#### **Step 2: CLAHE (Contrast Limited Adaptive Histogram Equalization)**
```python
# Convert BGR → LAB color space
lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
l_channel, a, b = cv2.split(lab)

# Apply CLAHE only to L (luminance) channel
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
l_enhanced = clahe.apply(l_channel)

# Merge and convert back
lab_enhanced = cv2.merge([l_enhanced, a, b])
result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
```
- **Purpose**: Enhances local contrast without over-amplifying noise
- Works in **LAB color space** (separates luminance from color)
- `clipLimit=2.0`: Limits contrast amplification to prevent noise artifacts
- `tileGridSize=(8,8)`: Divides image into 8×8 tiles for localized processing

#### **Step 3: White Balance (Gray-World Algorithm)**
```python
# In LAB color space:
avg_a = np.average(result[:, :, 1])  # Average of 'a' channel (green-red)
avg_b = np.average(result[:, :, 2])  # Average of 'b' channel (blue-yellow)

# Shift a and b towards neutral (128)
result[:, :, 1] -= (avg_a - 128) * (L / 255.0) * 1.1
result[:, :, 2] -= (avg_b - 128) * (L / 255.0) * 1.1
```
- **Purpose**: Corrects color cast from different lighting conditions (warm/cool lights)
- **Gray-World Assumption**: Average color in a natural scene should be gray
- Adjusts chrominance channels while preserving luminance

#### **Augmentation Implementations**

| Augmentation | OpenCV Function | Parameters |
| :---- | :---- | :---- |
| Rotation | `cv2.getRotationMatrix2D()` + `cv2.warpAffine()` | ±15° random angle |
| Horizontal Flip | `cv2.flip(image, 1)` | Mirror across Y-axis |
| Brightness | `image * factor` | factor ∈ [0.7, 1.3] |
| Contrast | `(image - mean) * factor + mean` | factor ∈ [0.7, 1.3] |
| Color Jitter | HSV manipulation | H±10°, S×0.7-1.3, V×0.7-1.3 |

#### **Visual Pipeline Flow**
```
Input Image (500×500)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  PREPROCESSING                                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────────────┐            │
│  │ Resize  │ → │  CLAHE  │ → │ White Balance   │            │
│  │ 640×640 │   │ (LAB L) │   │ (Gray-World)    │            │
│  └─────────┘   └─────────┘   └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  AUGMENTATION (Random 50% chance each)                       │
│  ┌────────┐ ┌──────┐ ┌────────────┐ ┌──────────┐ ┌───────┐  │
│  │Rotation│ │ Flip │ │ Brightness │ │ Contrast │ │ Color │  │
│  │ ±15°   │ │ Horiz│ │   ×0.7-1.3 │ │  ×0.7-1.3│ │Jitter │  │
│  └────────┘ └──────┘ └────────────┘ └──────────┘ └───────┘  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
Output: 1 original + 3 augmented = 4 images per input
```

#### **Dataset Statistics (Post-Processing)**
| Metric | Value |
| :---- | :---- |
| Raw Images | 400 |
| Processed Images | 1600 (4× with augmentation) |
| Image Dimensions | 640×640 pixels |
| Color Space | BGR (OpenCV native) |
| Output Size | ~248 MB |

---

## **5. Functional Requirements**

### **FR-1: Image Acquisition & Processing**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-1.1 | Upload images from device (JPG, PNG, JPEG, max 5MB) | High |
| FR-1.2 | Capture images via PC webcam | High |
| FR-1.3 | Capture via phone camera through mobile browser | High |
| FR-1.4 | Validate image dimensions (min 224×224, max 4096×4096) | High |
| FR-1.5 | Apply preprocessing pipeline (resize, normalize, enhance) | High |
| FR-1.6 | Perform noise reduction for low-quality images | Medium |
| FR-1.7 | Display clear error messages for invalid files | Medium |

### **FR-2: Multi-Food Detection**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-2.1 | Detect Rice, Dal, Paneer, Roti in single image | Critical |
| FR-2.2 | Display bounding boxes with labels | High |
| FR-2.3 | Show confidence scores (threshold: 0.5) | High |
| FR-2.4 | Detect multiple instances of same class (e.g., 3 roti pieces) | High |
| FR-2.5 | Handle "no food detected" gracefully with user message | Medium |

### **FR-3: Portion Estimation**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-3.1 | Estimate weight in grams for each detected item | Critical |
| FR-3.2 | Target accuracy: ≤20% MAPE on test set | High |
| FR-3.3 | Fallback to S/M/L categories if regression fails | Low |

### **FR-4: Nutrition Calculation**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-4.1 | Calculate calories per detected item | Critical |
| FR-4.2 | Provide macro breakdown (Protein, Carbs, Fats) | High |
| FR-4.3 | Display total meal nutrition summary | High |
| FR-4.4 | Use local JSON database for nutrition lookup | High |

### **FR-5: User Correction & Feedback**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-5.1 | Display results in editable format | High |
| FR-5.2 | Allow manual portion adjustment via sliders (50%-150% range) | High |
| FR-5.3 | Allow direct gram entry via text input | Medium |
| FR-5.4 | Recalculate nutrition dynamically on changes | High |
| FR-5.5 | Log both AI estimates and user corrections | Medium |

### **FR-6: Meal Logging & History**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-6.1 | Save analyzed meals with timestamp | High |
| FR-6.2 | Store food items, weights, and nutrition data | High |
| FR-6.3 | Provide chronological meal history view | Medium |
| FR-6.4 | Allow edit/delete of logged meals | Medium |

### **FR-7: Simple Dashboard**

| ID | Requirement | Priority |
| :---- | :---- | :---- |
| FR-7.1 | Display daily calorie total | Medium |
| FR-7.2 | Show progress bar vs. default target (2000 kcal) | Medium |
| FR-7.3 | Display weekly trend line chart | Low |
| FR-7.4 | List meals logged today | Medium |

---

## **6. Non-Functional Requirements**

### **NFR-1: Performance**

| Metric | Target |
| :---- | :---- |
| End-to-end processing (upload → results) | < 3 seconds (GPU), < 5 seconds (CPU) |
| YOLO detection | < 500ms |
| Portion estimation | < 100ms |
| Nutrition lookup | < 50ms |
| Page load time | < 2 seconds (4G network) |
| First Contentful Paint (FCP) | < 1.5 seconds |

### **NFR-2: Accuracy**

| Metric | Target |
| :---- | :---- |
| Detection mAP@50 | > 0.85 (4 food classes) |
| Portion estimation MAPE | ≤ 20% |
| Calorie estimation error | ± 20% |

### **NFR-3: Usability**

- Mobile-first responsive design (320px to 4K)
- Simple and intuitive user interface
- Clear visual feedback for all actions
- One-handed operation support on mobile

### **NFR-4: Reliability**

| Requirement | Description |
| :---- | :---- |
| Error Handling | Graceful handling of all error conditions |
| Data Validation | All inputs validated before processing (Pydantic) |
| Uptime Target | 95% (acceptable for free-tier hosting) |
| Health Endpoint | `/health` for monitoring |

### **NFR-5: Code Quality**

| Metric | Target |
| :---- | :---- |
| Coding Standard | Google Python Style Guide |
| Type Hints | Required on all functions |
| Docstrings | Google style, all public methods |
| Test Coverage | > 80% for non-ML code |
| Pylint Score | > 9.0/10 |

### **NFR-6: Portability**

- Fully Dockerized application
- Environment consistency (dev = prod)
- All config values externalized (YAML, .env)
- No hardcoded paths or thresholds

---

## **7. External Interface Requirements**

### **7.1 User Interface Components**

| Component | Description |
| :---- | :---- |
| **Home/Dashboard** | Calories remaining, today's macros, recent meals |
| **Scan Page** | Camera capture with bounding box overlay |
| **Results View** | Detection results with nutrition breakdown, portion sliders |
| **History Page** | Chronological meal log with edit/delete |
| **Profile** | User settings, goals, dietary preferences |

### **7.2 API Endpoints**

| Endpoint | Method | Description |
| :---- | :---- | :---- |
| `/api/v1/analyze` | POST | Analyze food image |
| `/api/v1/meals` | GET | Retrieve meal history |
| `/api/v1/meals` | POST | Save meal log |
| `/api/v1/meals/{id}` | PUT | Update meal |
| `/api/v1/meals/{id}` | DELETE | Delete meal |
| `/api/v1/dashboard/stats` | GET | Get dashboard statistics |
| `/api/v1/user/profile` | GET/POST | User profile management |
| `/health` | GET | Health check |

---

## **8. Database Schema**

### **8.1 Core Tables**

**Users Table**
| Column | Type | Description |
| :---- | :---- | :---- |
| id | INTEGER PRIMARY KEY | User ID |
| name | VARCHAR(100) | User name |
| height_cm | FLOAT | Height in cm |
| weight_kg | FLOAT | Weight in kg |
| age | INT | Age |
| activity_level | VARCHAR(20) | sedentary/moderate/active |
| goal | VARCHAR(20) | lose/maintain/gain |
| daily_target_kcal | INT | Default 2000 |

**Meals Table**
| Column | Type | Description |
| :---- | :---- | :---- |
| id | INTEGER PRIMARY KEY | Meal ID |
| user_id | INTEGER FK | Reference to users |
| image_url | VARCHAR(500) | Image path/URL |
| total_calories | FLOAT | Total meal calories |
| total_protein | FLOAT | Total protein (g) |
| total_carbs | FLOAT | Total carbs (g) |
| total_fats | FLOAT | Total fats (g) |
| logged_at | TIMESTAMP | Meal timestamp |

**Food Items Table**
| Column | Type | Description |
| :---- | :---- | :---- |
| id | INTEGER PRIMARY KEY | Item ID |
| meal_id | INTEGER FK | Reference to meals |
| food_class | VARCHAR(50) | rice/dal/paneer/roti |
| confidence | FLOAT | Detection confidence |
| ai_portion_grams | FLOAT | AI estimated weight |
| user_portion_grams | FLOAT | User corrected weight |
| calories | FLOAT | Item calories |
| protein | FLOAT | Item protein |
| carbs | FLOAT | Item carbs |
| fats | FLOAT | Item fats |

---

## **9. Development Standards**

### **9.1 Google Python Style Guide**

We strictly follow the **Google Python Style Guide** for consistency and maintainability.

**Key Rules:**
- **Type Hints:** Required on all function arguments and return values
- **Docstrings:** Google style for all public modules, classes, functions
- **Naming:** `lowercase_with_underscores` for functions/variables, `CapitalizedWords` for classes
- **Line Length:** Maximum 100 characters
- **Imports:** Organized in 3 groups (standard, third-party, local)

### **9.2 Pre-commit Hooks**

Enforced tools:
- **Black:** Code formatting (line-length=100)
- **isort:** Import sorting (profile=black)
- **mypy:** Static type checking (--strict)
- **Pylint:** Code quality (score > 9.0)

### **9.3 Git Workflow**

**Branching:**
- `main` - Production-ready code
- `dev` - Integration branch
- `feature/*` - Feature branches

**Commit Convention:**
```
<type>(<scope>): <subject>

Types: feat, fix, docs, style, refactor, test, chore
```

---

## **10. Deployment Strategy**

### **10.1 Local Development**

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

### **10.2 Docker Configuration**

**Dockerfile (Backend):**
```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ai_engine/ ./ai_engine/
COPY data/ ./data/
COPY ml/weights/ ./ml/weights/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=development
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### **10.3 Cloud Deployment**

| Platform | Type | Use Case |
| :---- | :---- | :---- |
| **Render** | Docker | Backend API (free tier: 512MB RAM) |
| **Railway** | Docker | Backend API (alternative) |
| **Hugging Face Spaces** | Docker | Backend with GPU option |
| **Vercel** | Static | Frontend React build |
| **Netlify** | Static | Frontend alternative |

**Environment Variables:**
```
ENV=production
API_URL=https://nutrisnap-api.onrender.com
MODEL_PATH=/app/ml/weights/
```

### **10.4 Mobile Access**

Users access the web app via mobile browser:
1. Open `https://nutrisnap.app` on phone
2. Responsive React UI adapts to mobile viewport
3. Camera capture uses HTML5 `<input type="file" accept="image/*" capture="environment">`
4. Browser opens native camera app
5. Image uploaded to backend via HTTPS

---

## **11. Appendices**

### **11.1 Dataset Preparation**

#### **Data Sources**
| Dataset | Description | Images |
| :---- | :---- | :---- |
| **Khana** | Indian food classification | Filter 75-100 per class |
| **FoodSeg103** | Ingredient segmentation | Extract bounding boxes |
| **Custom** | Team-collected photos | Gap filling |

#### **Annotation Process**
- **Tool:** Roboflow (free tier) or CVAT
- **Format:** YOLO (class_id x_center y_center width height)
- **Target:** 300-400 annotated images (75-100 per class)
- **Time:** ~4-6 hours with 4 team members

#### **Dataset Split**
| Split | Percentage | Images |
| :---- | :---- | :---- |
| Training | 70% | ~210-280 |
| Validation | 15% | ~45-60 |
| Test | 15% | ~45-60 |

### **11.2 Target Food Classes (v1)**

**4 Core Classes:**
- **Rice** - Cooked white rice, jeera rice
- **Dal** - Dal makhani, toor dal, chana dal
- **Paneer** - Paneer butter masala, paneer tikka, plain paneer
- **Roti** - Chapati, phulka, whole wheat roti

### **11.3 Technology Stack Summary**

| Layer | Technology | Version |
| :---- | :---- | :---- |
| Frontend | React, Vite, TailwindCSS, Recharts | 18.x, 5.x, 3.x, 2.x |
| Backend | Python, FastAPI, SQLAlchemy, Pydantic | 3.10+, 0.110+, 2.0+, 2.6+ |
| AI Engine | CrewAI, PyTorch, Ultralytics, XGBoost | Latest, 2.2+, 8.2.x, 2.0+ |
| CV/DIP | OpenCV | 4.9+ |
| Database | SQLite (dev) / PostgreSQL (prod) | 3.x / 15+ |
| Container | Docker, Docker Compose | Latest |

### **11.4 Glossary**

| Term | Definition |
| :---- | :---- |
| **Agent** | Autonomous software component with specific role |
| **Bounding Box** | Rectangular coordinates (x1, y1, x2, y2) defining object location |
| **CLAHE** | Contrast Limited Adaptive Histogram Equalization |
| **Inference** | Running trained model on new data to make predictions |
| **MAPE** | Mean Absolute Percentage Error - accuracy metric for regression |
| **Orchestration** | Coordination of multiple agents to complete workflow |
| **Transfer Learning** | Using pre-trained weights as starting point for custom training |

### **11.5 Future Roadmap**

| Phase | Features | Timeline |
| :---- | :---- | :---- |
| **v1.0** | 4-food detection, portion estimation, logging, dashboard | Current |
| **v2.0** | 40+ foods, meal planning, AI chatbot, recipe generator | Future |
| **v3.0** | Native mobile apps, barcode scanning, social features | Long-term |

---

**Document Prepared By:** NutriSnap AI Development Team  
**Last Updated:** February 09, 2026  
**Status:** Ready for Implementation