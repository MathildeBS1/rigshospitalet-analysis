# Prep Time — Two Different Things

There are two distinct "prep" windows in the data. Conflating them is a common mistake.

## 1. OR Room Prep (between cases)

`ts_or_prep_start → ts_or_prep_done`

Room setup that happens during turnaround, *before* the next patient arrives. This is what `eda/linus/or_turnaround.py` measures as part of the idle time breakdown.

**Coverage caveat:** `ts_or_cleaning_start` and `ts_or_cleaned` are frequently missing or entered as identical timestamps (zero-duration cleaning) — data quality noise, not reality.

## 2. Patient-Side Prep (inside the OR)

`ts_patient_in_or → ts_procedure_start`

Time from patient entering the OR to knife time. Includes anesthesia setup. Timestamps here are more reliably recorded since anesthesia staff enter them.

This is likely what Mathilde's prep gap analysis (+13.8 min vs +4.3 min in-OR) is measuring.

## Why It Matters for ML

The staff count (r=+0.49) and equipment count (r=+0.27) correlations Mathilde found need to be verified against which gap she actually computed. The ML target for prep time prediction should match the right window — confirm with Mathilde before building features.
