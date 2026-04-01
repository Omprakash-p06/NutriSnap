# V1 Requirements

## 1. Grok API Integration (Validation)
- [ ] **GROK-01**: Backend securely calls Grok API with both the baseline AI detections (food names, estimated grams) and the originally uploaded picture for full multimodal verification.
- [ ] **GROK-02**: Backend parses Grok API response to update baseline calories, protein, carbs, and fats.
- [ ] **GROK-03**: Fallback gracefully to `nutrition.json` if Grok API is unavailable or rate-limited.

## 2. Personal Health Profiles (User)
- [ ] **USR-01**: User can enter and update their height, weight, and BMI.
- [ ] **USR-02**: User can select a primary health goal (Weight Loss, Weight Gain, Maintenance).
- [ ] **USR-03**: System calculates static daily macro targets (calories, protein, carbs, fats) based on goal & BMI.

## 3. Meal Evaluation & Tracking (Evaluation)
- [ ] **EVAL-01**: After a meal is analyzed by the AI, the UI displays whether the meal matches the user's macro target trajectory.
- [ ] **EVAL-02**: User's dashboard visually compares total consumed daily nutrition against daily macro targets.
- [ ] **EVAL-03**: User can view a historical timeline of their adherence to their health goals.

## 4. Customized Meal Planning (Planning)
- [ ] **PLAN-01**: System prompts user for a personalized diet suggestion.
- [ ] **PLAN-02**: Backend uses Grok API to generate a realistic full-day meal plan based on the user's deficit/surplus goals.
- [ ] **PLAN-03**: User can accept or regenerate AI meal suggestions.
