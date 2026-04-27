# Tech Stack - NutriSnap

## Backend
- **Framework**: FastAPI (Python 3.11+)
- **Inference Engine**: PyTorch / ONNX
- **ML Pipeline**:
  - **YOLOv8**: Object detection for food items.
  - **SAM 2**: High-precision instance segmentation.
  - **GLPN**: Monocular depth estimation for volume calculation.
  - **ViT Regressor**: Direct weight/calorie estimation from visual features.
  - **Gemini 2.0 Flash**: Multi-modal LLM for nutritional reasoning and user interaction.
- **Optimization**: Sequential model execution with `torch.cuda.empty_cache()` to fit 4GB VRAM.

## Frontend
- **Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS
- **PWA**: Vite PWA Plugin for offline-first and mobile-responsive experience.
- **State Management**: React Context / Hooks.

## Infrastructure
- **Database**: MongoDB Atlas (User profiles, History).
- **Data Storage**: Local CSV/JSON for ingredient mapping.
- **CI/CD**: GitHub Actions.
