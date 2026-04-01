# Proposed Roadmap

**4 phases** | **12 requirements mapped** | All active requirements covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Infrastructure: User Profiles (Completed) | Establish health profiles and daily macro targets. | USR-01, USR-02, USR-03 | 2 |
| 2 | Intelligence: Grok Integration | Add Grok validation for existing computer-vision analysis. | GROK-01, GROK-02, GROK-03 | 3 |
| 3 | Application: Meal Evaluation | Feed macro computations back into the daily tracking UI. | EVAL-01, EVAL-02, EVAL-03 | 2 |
| 4 | Features: AI Meal Planner | Construct the Grok-powered daily meal generator workflow. | PLAN-01, PLAN-02, PLAN-03 | 2 |

### Phase Details

**Phase 1: Infrastructure: User Profiles (Completed)**
*Goal: Establish health profiles and daily macro targets.*
Requirements: USR-01, USR-02, USR-03
Success criteria:
1. User can persist BMI and Goals in the datastore.
2. The User model cleanly calculates internal daily baseline macros.

**Phase 2: Intelligence: Grok Integration**
*Goal: Add Grok validation for existing computer-vision analysis.*
Requirements: GROK-01, GROK-02, GROK-03
Success criteria:
1. Valid credentials for Grok API loaded securely.
2. `FoodAnalysisService` defers validation to Grok logic.
3. System smoothly skips Grok and returns local estimations on network failure.

**Phase 3: Application: Meal Evaluation**
*Goal: Feed macro computations back into the daily tracking UI.*
Requirements: EVAL-01, EVAL-02, EVAL-03
Success criteria:
1. The analysis screen surfaces a "goal alignment" badge.
2. Dashboard graphs display remaining daily allowances for calories and macros instead of just raw totals.

**Phase 4: Features: AI Meal Planner**
*Goal: Construct the Grok-powered daily meal generator workflow.*
Requirements: PLAN-01, PLAN-02, PLAN-03
Success criteria:
1. "Generate Plan" button fetches a schedule of meals tailored to user macros.
2. Grok responses strictly surface realistic Indian-cuisine oriented plans matching NutriSnap's domain.
