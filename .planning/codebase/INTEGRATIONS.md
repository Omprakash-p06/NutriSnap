# Integrations & External Services

## Machine Learning Integration
- **ultralytics/yolov8**: Integrated via `torch.hub` for food detection inference.
- **depth-anything-v2**: Integrated via `torch.hub` for depth estimation.
- **SAM (Segment Anything Model)**: Pre-trained weights integration for segmentation.

## Data Integration
- **Nutrition Database**: Static JSON file loaded into memory (`data/nutrition_db/nutrition.json`). Acts as a proxy for an external nutrition lookup service.

*Currently there are no dynamic external 3rd-party webhook endpoints or APIs defined in the codebase. All processing is kept locally to the machine.*
