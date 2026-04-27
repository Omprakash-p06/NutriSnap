# Requirements: NutriSnap

## Functional Requirements

### P0: Core Foundations (MVP)
- **REQ-P0-01: Image → Mass API**: Create a FastAPI endpoint that accepts an image and returns the estimated food mass using the existing model.
- **REQ-P0-02: Calorie Conversion**: Implement mass-to-calorie conversion using a lookup table/density mapping.
- **REQ-P0-03: Manual Logging**: Provide CRUD endpoints for users to log meals manually by searching a pre-built food database (USDA/JSON).
- **REQ-P0-04: User Profiles**: Implement JWT authentication and profile management (age, weight, height, goal).
- **REQ-P0-05: Calorie Targeting**: Automatically calculate daily calorie requirements using the Mifflin-St Jeor equation.

### P1: Advanced Analysis (V1.1)
- **REQ-P1-01: Multi-food Detection**: Integrate a pre-trained YOLOv5 model to detect multiple foods, crop them, and pass each to the mass model.
- **REQ-P1-02: Ingredient Breakdown**: Use a mapping system (CSV) to decompose food types into ingredients and macro profiles.
- **REQ-P1-03: AI Assistant**: Integrate Gemini 2.0 Flash to provide conversational nutrition advice based on meal data and user goals.

### P2: Personalization & UX (V1.2)
- **REQ-P2-01: Meal Planner**: Implement a rule-based engine to suggest meals from a recipe database based on calorie/macro gaps.
- **REQ-P2-02: Progress Dashboard**: Create a visualization layer (Recharts) to track daily/weekly intake vs. targets.

## Non-Functional Requirements
- **NFR-01: No Retraining**: The system must use existing model weights; no additional training of the mass model is permitted.
- **NFR-02: Latency**: Normal inference (single food) should target < 200ms (excluding LLM calls).
- **NFR-03: Accessibility**: The web platform must be responsive and work on standard desktop/mobile browsers.
- **NFR-04: Security**: User data must be protected via JWT and secure API practices.

## Success Criteria
1. Single-food image upload returns mass and calories within 2 seconds.
2. Users can login and see their personalized calorie target.
3. Multi-food detection correctly identifies at least 2 items on a plate.
4. AI assistant provides context-aware advice for detected meals.
