# Overtime Prediction

Predict whether a case will run over its planned time slot.

**Target:** binary `overtime_minutes > 0`, or regression on `overtime_minutes` directly

**Features:** same as prep time regression (staff count, equipment count, specialty, diagnosis group, is_acute, patient age) + planned duration

**Interpretability requirement:** clinical staff won't trust a black box — pair any gradient boosted model with SHAP values or a shallow decision tree so outputs are explainable on shift.

**Note:** explicitly suggested as a "key factor analysis" in the case brief.
