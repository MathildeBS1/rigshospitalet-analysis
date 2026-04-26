# Analysis Plan — Linus

## What we're trying to answer

Rigshospitalet schedules surgeries in advance. They estimate how long each surgery will take and block out time in the OR accordingly. The question is: **how wrong are those estimates, and what can be done about it?**

---

## The data

Two CSV files in `data/`:

- `completed_operations.csv` — 133,158 rows, one row per procedure. Since some cases involve multiple procedures, there are **120,868 unique cases** (use `case_id` to deduplicate).
- `cancelled_operations.csv` — 575 rows of cancelled cases.

The data covers **2 years: 2024-01-01 to 2025-12-31**, across **32 surgical specialties** and **129 OR rooms**.

Load it with:

```python
import sys
sys.path.insert(0, 'src')
from data.loader import load_completed
df = load_completed()
cases = df.unique(subset=['case_id'], keep='first')
```

### Key columns

| Column | What it means |
|---|---|
| `case_id` | Unique ID per case (deduplicate on this) |
| `specialty` | Surgical specialty (32 unique values) |
| `or_room` | Which OR room (129 rooms) |
| `date` | Date of the operation |
| `is_acute` | True/False — was this an emergency case? (20.6% are acute) |
| `patient_age` | Patient age in years (0–107, mean 55) |
| `procedure_text_id` | The specific procedure performed (2,206 unique types) |
| `diagnosis_group` | Broad diagnosis category |
| `delay_minutes` | How many minutes late the case started (as recorded by staff) |
| `overtime_minutes` | See note below — **not** what it sounds like |
| `delay_reason` | Free-text reason for the delay |
| `staff_*` | ~30 boolean columns — which staff roles were present |
| `resource_*` | ~180 boolean columns — which equipment was used |

### Key timestamps

All timestamps follow the format `ts_<event>`. The most important ones:

| Timestamp | Meaning | Coverage |
|---|---|---|
| `ts_patient_in_or_planned` | When the patient was *supposed* to enter the OR | 99.7% |
| `ts_patient_in_or` | When the patient *actually* entered the OR | 99.6% |
| `ts_procedure_start` | Knife time — surgery begins | 99.4% |
| `ts_procedure_end` | Surgery ends | 99.4% |
| `ts_patient_leaves_or_planned` | When the patient was *supposed* to leave | 99.7% |
| `ts_patient_leaves_or` | When the patient *actually* left | 99.6% |
| `ts_anesthesia_start` | Anesthesia begins (null if no anesthesia) | 64.8% |
| `ts_or_prep_start` / `ts_or_prep_done` | OR room setup — **unreliable, do not use** | ~90% but 62% have identical start/end |

### One important correction about `overtime_minutes`

The `overtime_minutes` column sounds like "how much longer than planned the surgery took" — but it actually measures **how late the OR room finished overall**. That includes both starting late AND running long. Mathematically:

```
overtime_minutes = start_delay + duration_gap
```

where:
- `start_delay` = `ts_patient_in_or` − `ts_patient_in_or_planned`
- `duration_gap` = actual in-OR time − planned in-OR time

This was confirmed: the difference between `overtime_minutes` and the computed sum is 0 on every row. So when reporting numbers, always separate these two components rather than citing `overtime_minutes` as if it means one thing.

---

## What we found in the data (the problem)

There are **two distinct failures** in OR scheduling, not one.

### Failure 1: Cases start late

Compute with:
```python
start_delay = ts_patient_in_or - ts_patient_in_or_planned
```

| Metric | Value |
|---|---|
| % of cases starting late | **73.1%** |
| % starting more than 15 min late | **48.9%** |
| Mean start delay | **+20.7 min** |
| Median start delay | **+15.0 min** |

This has nothing to do with how long the surgery takes. The patient simply isn't in the OR when they're supposed to be.

### Failure 2: Surgeries take longer than planned

Compute with:
```python
actual_inor_min  = ts_patient_leaves_or      - ts_patient_in_or
planned_inor_min = ts_patient_leaves_or_planned - ts_patient_in_or_planned
duration_gap     = actual_inor_min - planned_inor_min
```

| Metric | Value |
|---|---|
| % of cases running longer than planned | **53.9%** |
| % running more than 15 min over | **25.5%** |
| Mean duration gap | **+4.3 min** |
| Median duration gap | **+2.0 min** |

The mean looks small, but it's an average — some cases are fine, others run wildly over. The p90 gap is +44 min.

### Are the two failures related?

A natural question: is Failure 2 caused by Failure 1? If a case starts late, does the surgery end up running over its planned duration because of the knock-on pressure?

No. We checked:

```python
# Group cases by how late they started, compare duration gap within each group
corr(start_delay_min, duration_gap_min)  # r = -0.01
```

| Start delay bucket | % running over planned duration | Mean duration gap |
|---|---|---|
| On time or early | 50.1% | +4.9 min |
| 1–15 min late | 50.3% | +5.0 min |
| 16–30 min late | 52.2% | +4.2 min |
| 31–60 min late | 59.9% | +3.5 min |
| 60+ min late | 60.5% | +3.4 min |

Cases that start on time still run over 50% of the time — almost the same rate as cases starting an hour late. The correlation between start delay and duration gap is r = −0.01, effectively zero.

**These are two independent failures.** The duration estimate is broken regardless of when the case starts. That means Rigshospitalet has two separate problems to fix, not just one root cause.

### The combined effect

Both problems stack:

| Metric | Value |
|---|---|
| % of OR rooms finishing after planned time | **68.0%** |
| Mean OR room overrun | **+25.7 min** |

### What the actual in-OR time looks like

| | mean | median | p25 | p75 | p90 |
|---|---|---|---|---|---|
| Actual in-OR time | 109 min | 82 min | 38 min | 148 min | 238 min |
| Planned in-OR time | 105 min | 83 min | 39 min | 142 min | 220 min |

The wide spread (38 min at p25 to 238 min at p90) reflects how different surgeries are from each other. A cataract removal and a heart operation are not the same thing.

### In-OR time breaks into three phases

```
ts_patient_in_or → ts_procedure_start → ts_procedure_end → ts_patient_leaves_or
     patient prep          actual surgery         post-procedure
      (32 min avg)           (61 min avg)            (16 min avg)
                         = 109 min total
```

The biggest driver of prep time is **anesthesia**:

| | n cases | Mean prep time | Mean total in-OR time |
|---|---|---|---|
| No anesthesia | 44,767 | 12 min | 44 min |
| With anesthesia | 74,565 | 44 min | 149 min |

Knowing whether anesthesia is planned nearly doubles the expected OR time. This is a huge scheduling signal that should be used explicitly.

---

## The analysis plan (5 parts)

### Part 1 — Prove the problem clearly

Show the two failures separately — late starts and wrong duration estimates — broken down by specialty. Convert the gaps into total hours lost across all 120k cases to give Rigshospitalet a concrete scale.

**Columns to use:** `specialty`, `ts_patient_in_or`, `ts_patient_in_or_planned`, `ts_patient_leaves_or`, `ts_patient_leaves_or_planned`

---

### Part 2 — Which procedures are most wrong

The hospital's current duration estimates are systematically off for specific procedure types. For each procedure (filtered to n ≥ 50 cases for reliability), compute:

```
mean actual in-OR time  vs  mean planned in-OR time  →  gap
```

This produces a simple lookup table: *"Procedure X is always scheduled 20 minutes short — plan 20 more."* Schedulers can use this immediately with no technology.

**Columns to use:** `procedure_text_id`, `actual_inor_min` (computed), `planned_inor_min` (computed), `specialty`

**Filter:** Procedures with at least 50 historical cases (gives 434 procedures with stable estimates).

---

### Part 3 — The cascade effect

When the first surgery of the day starts late, does the whole day fall apart?

Assign each case a position number within its OR room's daily schedule (1 = first case of the day). Then check whether first-case delay predicts how delayed later cases are.

**Columns to use:** `or_room`, `date`, `ts_patient_in_or_planned`, `delay_minutes`

**Method:** Sort cases by `[or_room, date, ts_patient_in_or_planned]`, assign position with `.rank("ordinal").over(["or_room", "date"])`, correlate first-case delay with mean delay of later cases.

---

### Part 4 — Can a machine learning model do better?

Short answer: **barely, with the data we have.**

We tested how much of the variance in actual in-OR time each feature explains (R²):

| Feature | R² |
|---|---|
| `procedure_text_id` alone | **0.803** |
| `specialty` alone | 0.391 |
| `diagnosis_group` alone | 0.355 |
| Anesthesia flag alone | 0.284 |

The procedure type already explains 80% of variance. After accounting for that, the remaining features add almost nothing:

| Feature | Correlation with residual error |
|---|---|
| `patient_age` | r = 0.00 (literally nothing) |
| `staff_count` (sum of `staff_*` columns) | r = +0.12 |
| `resource_count` (sum of `resource_*` columns) | r = +0.06 |

The residual after knowing procedure type is still ±26 minutes (mean absolute error) and ±42 minutes (std dev). But no feature in the data explains that residual. This is surgical noise — complications, unexpected findings, surgeon pace — that cannot be predicted from a pre-operative spreadsheet.

A machine learning model trained on this data would achieve roughly R² ≈ 0.83–0.85 at best, vs the lookup table's 0.80. The 3–5% improvement is not worth the complexity.

**The lookup table is the right tool for this data.**

---

### Part 5 — What data should Rigshospitalet collect

The reason ML doesn't help is that the *right* features are missing. This is itself an actionable finding — here's what to collect and why:

| Missing feature | Why it matters |
|---|---|
| **Surgeon identity** | Different surgeons perform the same procedure at very different speeds. This is likely the biggest source of within-procedure variance. |
| **Patient complexity** (ASA score, BMI, comorbidities) | A healthy 40-year-old and a frail 80-year-old having the same procedure will not take the same time. ASA scores exist in clinical records — they're just not in this dataset. |
| **More granular procedure coding** | Some `procedure_text_id` values group together cases that are actually very different in practice. More detailed coding would reduce within-group variance. |

With surgeon identity and ASA score added, a prediction model could plausibly reach R² ≈ 0.90+, which would be worth deploying. The recommendation to Rigshospitalet: start logging these fields consistently in the OR management system, and revisit the model in 1–2 years once there's enough data.
