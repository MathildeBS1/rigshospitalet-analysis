# Prep Time — Definitions and Data Quality

## The timestamp flow (official)

```plaintext
ts_or_prep_planned_start  planned start of OR room preparation
ts_or_prep_start          actual start of OR room preparation
ts_or_prep_done           OR room preparation completed (room ready)
ts_patient_in_or          patient arrives in OR
ts_anesthesia_start       anesthesia begins
ts_anesthesia_ready       patient sedated, ready for surgery
ts_procedure_start        first surgical procedure begins (knife time)
```

## Phase 1: OR room prep — `ts_or_prep_start → ts_or_prep_done`

Officially: "starting the preparation of the OR → preparations completed."

**Unreliable.** 62% of cases (68,514 / 110,037) have identical start and end timestamps. We don't know if staff clicked both at the start, both at the end, or something in between. The direction of any bias is unknown. Do not use as a feature or target.

## Phase 2: Mathilde's window — `ts_or_prep_start → ts_patient_in_or`

Spans room prep + the gap after the room is ready but before the patient arrives. The window starts at `ts_or_prep_start`, which is unreliable for 62% of cases (same value as `ts_or_prep_done`). Since the direction of the bias is unknown, we can't say whether her actual prep times are understated or overstated. Her findings are directionally plausible but not a clean ML target.

## Phase 3: Patient-side prep — `ts_patient_in_or → ts_procedure_start`

"Patient arrives at OR → first surgical procedure begins." Includes anesthesia (where applicable).

**The right ML target.** 99.4% coverage (119,965 cases), only 2% zero-duration, sensible distribution:

| mean   | median | p25    | p75    | p90    |
| ------ | ------ | ------ | ------ | ------ |
| 32 min | 27 min | 10 min | 47 min | 67 min |

Anesthesia sub-phases (where recorded): `ts_anesthesia_start → ts_anesthesia_ready` averages 29 min; `ts_anesthesia_ready → ts_procedure_start` averages 18 min. Not all operations require anesthesia, which explains the wide p25–p75 spread.

## Implication for ML

Use `ts_patient_in_or → ts_procedure_start` as the prep time target. Staff count (r=+0.49) and equipment count (r=+0.27) correlations Mathilde found should be re-verified against this window before building features.
