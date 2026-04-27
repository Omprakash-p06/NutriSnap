# Phase 5 Research: Evaluation & Verification

Research into robust evaluation frameworks and plausibility verification for the NutriSnap nutrition estimation pipeline.

## Standard Stack

- **Metrics**: `scikit-learn` for $R^2$ and MAE; `scipy.stats` for Spearman correlation and Bias.
- **Visualization**: `matplotlib` and `seaborn` for Residuals vs. Fitted and Predicted vs. Actual plots.
- **Rule Engine**: Simple Python validator using Atwater factors.
- **LLM Verification**: `google-generativeai` (Gemini 1.5 Flash) for multimodal visual QA.

## Architecture Patterns

### 1. Regression Diagnostics Suite
A standard report for each fold and the ensemble must include:
- **MAE & MAPE**: Accuracy measure.
- **Spearman Rho**: Measures rank correlation (does the model correctly identify high-calorie vs. low-calorie meals even if absolute values are off?).
- **Variance Split**: Compare `Var(Preds)` vs. `Var(Actuals)`. If `Var(Preds) < 0.1 * Var(Actuals)`, the model has collapsed to constant-prediction (mean-estimation).
- **Residual Analysis**: Identify if the model consistently underestimates large meals (negative bias at high values).

### 2. Atwater Validator (Rule-Based)
Implementation of the "Nutrition Sanity Check":
- **Constraint**: `abs(Pred_Kcal - (4*P + 4*C + 9*F)) / Pred_Kcal < 0.15`
- **Density Gate**: `Pred_Kcal / volume_cm3` should be within `[0.1, 8.0]` (kcal/mL). Values outside this are physically implausible for most foods.
- **Volume Logic**: `volume_cm3 / area_cm2` should be within realistic height bounds (e.g., 0.5cm to 15cm).

### 3. LLM VQA Fallback (Gemini Flash)
When the rule-engine flags a result as "high-risk" (implausible) or the model confidence is low:
- **Prompt**: "Identify the food in this image. List ingredients and estimate grams. Provide total calories, protein, carbs, and fat."
- **Verification**: Use the LLM output as a "second opinion." If the model and LLM differ by >50%, flag for human review.

## Don't Hand-Roll

- **Plotting Routines**: Use `seaborn.jointplot` for pred-vs-actual; don't build custom scatter/histogram overlays.
- **Atwater Basics**: Use 4-4-9; don't attempt complex metabolizable energy delta logic unless necessary (it introduces too much variance).

## Common Pitfalls

- **Metric Masking**: High $R^2$ can mask severe bias in small classes (e.g., snacks).
  - **Fix**: Perform "Binned Error Analysis" (split metrics by calorie ranges: <200, 200-800, >800).
- **LLM Hallucination**: LLMs are overconfident in calorie numbers.
  - **Fix**: Ask the LLM for *ingredients* first, then calculate macros from its ingredients, or use its output only as a range-gate.

## Code Examples

### Plausibility Engine
```python
def validate_realism(preds, volume, area):
    """
    preds: {'calories', 'protein', 'fat', 'carbs'}
    Returns: (is_plausible, reason)
    """
    # 1. Atwater Check
    kcal_calc = 4 * preds['protein'] + 4 * preds['carbs'] + 9 * preds['fat']
    if abs(preds['calories'] - kcal_calc) / (preds['calories'] + 1e-6) > 0.2:
        return False, "Atwater inconsistency"
    
    # 2. Density Check (kcal/cm3)
    density = preds['calories'] / (volume + 1e-6)
    if density > 9.0 or (volume > 50 and density < 0.05):
        return False, f"Implausible energy density: {density:.2f}"
        
    return True, "OK"
```

## Confidence Levels

- **Diagnostic Metrics**: HIGH. Standard statistical verification.
- **Rule Engine**: HIGH. Physics/Biology based constraints are very reliable.
- **LLM Fallback**: MEDIUM. Dependent on API availability and latency.

## RESEARCH COMPLETE
Summary:
- Diagnostics: MAE, Spearman, Residual Plots, Pred Variance.
- Validator: Atwater (4-4-9) + Energy Density gates.
- Fallback: Gemini Flash VQA for "High Risk" cases.
