# Technical Concerns & Constraints

- **VRAM (4GB)**: The absolute limit for local model inference. Requires aggressive cache clearing.
- **Inference Latency**: The 4-model pipeline + Gemini API call takes ~3-5 seconds. UI must provide high-quality feedback during wait times.
- **Depth Accuracy**: Monocular depth estimation is an approximation; results should be presented as "estimates" with user override options.
- **API Dependency**: Heavy reliance on Gemini for reasoning means internet connectivity is required for full functionality.
