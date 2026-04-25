# Prep Time Regression

Predict required prep time per operation so the hospital can replace its flat/wrong planned prep allocation.

**Target:** actual prep time (`ts_or_prep_done - ts_or_prep_start`)

**Features:** staff count, equipment count, specialty, diagnosis group, is_acute, patient age

**Models:** linear regression (interpretable, directly actionable) + gradient boosting (how much non-linearity is there?)

**Grounding:** Mathilde found prep gap is +13.8 min vs +4.3 min in-OR, and staff count correlates at r=+0.49 with actual prep time while the schedule treats it as ~zero.
