# Prep Time Regression

> **Superseded by `total-inor-prediction.md`**

Originally proposed predicting patient-side prep (`ts_patient_in_or → ts_procedure_start`) from staff count, equipment count, and procedure features.

**Why we dropped it:** patient-side prep is largely just anesthesia duration (11.6 min without anesthesia vs 44.2 min with). The scheduler already knows whether anesthesia is planned, so this isn't truly invisible to the planning system. The clean ML target is total in-OR time instead.
