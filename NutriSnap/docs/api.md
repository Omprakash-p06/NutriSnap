# NutriSnap API Reference

*To be completed in Phase 6: FastAPI Delivery & Quality Hardening*

## Endpoints

### POST /predict
Submit a meal image for nutrition estimation. Returns 202 Accepted + image_id.

### GET /result/{image_id}
Poll for prediction results. Returns processing or completed state.
