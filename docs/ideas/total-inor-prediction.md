# Total In-OR Time Prediction

Predict total in-OR time (`ts_patient_in_or → ts_patient_leaves_or`) per case so the hospital can allocate more accurate scheduled slots.

**Target:** actual total in-OR time (minutes)

**Features:** procedure type, specialty, diagnosis group, is_acute, patient age, staff count, equipment count, whether anesthesia is planned

**Why it's the right ML target:**
- Clean data: both timestamps have >99% coverage and no quality issues
- The hospital already predicts this implicitly via the scheduled slot — an ML model just needs to do it better
- 54% of cases run over their planned slot, mean gap +4.7 min — there is real room for improvement
- All features are known pre-operatively, so predictions can be made at scheduling time

**Why not sub-phases:**
- Patient-side prep (`ts_patient_in_or → ts_procedure_start`) is largely anesthesia duration, which the scheduler already accounts for
- OR room setup (`ts_or_prep_start → ts_or_prep_done`) is unreliable — 62% same-timestamp entries of unknown direction
- Post-procedure is stable (~16 min, low variance) and uninteresting as a prediction target

**Output:** recommended slot duration per scheduled case, replacing or augmenting the current planning system.
