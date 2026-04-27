# System Architecture

## Monorepo Overview
NutriSnap uses a monorepo structure with a clear separation between the Python backend (ML & API) and the React frontend.

## ML Inference Pipeline
1. **Input**: Image upload via FastAPI endpoint.
2. **Detection**: YOLOv8 identifies objects and bounding boxes.
3. **Segmentation**: SAM 2 generates precise pixel masks for each object.
4. **Depth Analysis**: GLPN estimates depth; volume is derived from mask area and depth map.
5. **Estimation**: ViT Regressor predicts weight based on volume and food features.
6. **Reasoning**: Gemini 2.0 Flash processes the entire context (image + ML results) to provide the final nutritional analysis.

## VRAM Management
- **Strategy**: Sequential "Load-Run-Unload" pattern.
- **Constraint**: Models are loaded into VRAM one by one and cleared immediately after inference to respect the 4GB limit.
