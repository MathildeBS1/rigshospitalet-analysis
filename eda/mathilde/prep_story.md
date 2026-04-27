# The Prep Problem: How Misallocated Prep Time Cascades Through the OR Day

Source notebook: `prep_story.ipynb`

## Core story

The main finding is that the schedule is usually not too optimistic about time spent in the operating room itself. The bigger problem is earlier: the hospital often allocates no prep time, or too little prep time, before the patient enters the OR.

That under-allocation delays the first case, and that late start then shapes the rest of the day in one of three ways:

1. **Cascading:** the delay grows from case to case.
2. **One-time shock:** the delay carries forward but does not keep growing.
3. **Recovery:** the team absorbs the delay and gets back on track.

This matters because the effect is felt directly by patients, and also by doctors and staff who have to work under unnecessary schedule pressure once the day is already behind.

## Data and scope

The notebook uses a filtered surgical dataset with reliable prep timestamps:

- **38,190 surgical cases**
- **23 specialties**
- **Date range:** `2024-01-01` to `2025-12-31`

Only cases with usable prep and OR timing were kept. The analysis excludes non-surgical specialties, null or extreme timing gaps, and cases where prep timestamps were not reliable enough for measuring actual prep duration.

## How the calculations were performed

### Derived time measures

The notebook creates these core variables from planned and actual timestamps:

```text
planned_prep_min = ts_patient_in_or_planned - ts_or_prep_planned_start
planned_inor_min = ts_patient_leaves_or_planned - ts_patient_in_or_planned

actual_prep_min  = ts_patient_in_or - ts_or_prep_start
actual_inor_min  = ts_patient_leaves_or - ts_patient_in_or

start_delay_min  = ts_patient_in_or - ts_patient_in_or_planned
finish_delay_min = ts_patient_leaves_or - ts_patient_leaves_or_planned

prep_gap = actual_prep_min - planned_prep_min
inor_gap = actual_inor_min - planned_inor_min
```

In plain language:

- **Prep gap** measures how much more prep time was needed than the schedule allocated.
- **In-OR gap** measures how much more total OR time was used than planned after the patient entered the room.
- **Start delay** measures how late the patient actually entered the OR compared with the plan.

### 1. Is the problem prep or surgery?

The notebook groups cases by `procedure_name`, keeps procedures with at least `n >= 50`, and compares the average absolute prep gap with the average absolute surgery gap:

```text
prep_worse = abs(prep_gap) > abs(surgery_gap)
```

This tests whether the schedule is more wrong about room preparation or about the operation itself.

### 2. Zero-allocation analysis

The procedure-level table is then split into:

```text
zero_alloc    = procedures where planned_prep == 0
nonzero_alloc = procedures where planned_prep > 0
```

This isolates the procedures where the scheduler effectively assumed that no prep time was needed at all.

### 3. OR-day pattern classification

For each OR room and date, cases are ordered by planned patient-in time. The notebook then computes:

- case position in the day
- number of cases that day
- correlation between `position` and `start_delay_min`

Days with at least 3 cases are classified as:

```text
if corr(position, start_delay_min) > 0.5      -> Cascading
if corr(position, start_delay_min) < -0.2     -> Recovery
otherwise                                     -> One-time shock
```

This is what separates days where lateness compounds from days where the team recovers.

### 4. Patient waiting-time calculation

Patient waiting is defined as start delay:

```text
patient_wait = start_delay_min
```

The notebook then estimates the correctable part of the delay by subtracting the mean prep gap:

```text
corrected_delay = start_delay_min - mean(prep_gap)
```

It also estimates total lost patient time:

```text
total_wait_hours = sum(start_delay for late cases) / 60
correctable_hours = mean(prep_gap) * total_cases / 60
```

### 5. Predicting the prep time that should have been allocated

The notebook trains a `RandomForestRegressor` on **2024** cases and tests it on **2025** cases.

Predictors:

- `procedure_code`
- `staff_count`
- `resource_count`
- `has_anesthesia`
- `patient_age`
- `is_first_of_day`
- `is_last_of_day`
- `position`
- `total_cases_that_day`

The target is:

```text
actual_prep_min
```

So the model learns how much prep time a case is likely to need before the patient enters the OR.

## Results

### 1. The problem is prep, not surgery

- **88.2%** of procedures had a larger prep gap than surgery gap.
- **Mean prep gap:** `+22.8 min`
- **Mean surgery gap:** `+6.4 min`

This means the main scheduling error is upstream of surgery. The plan is much more wrong about getting the room ready than about how long the case itself takes once it starts.

### 2. Zero planned prep is the clearest failure mode

| Group | Procedures | Mean allocated prep | Mean actual prep | Mean prep gap | Mean surgery gap |
|---|---:|---:|---:|---:|---:|
| Zero planned prep | 111 | 0.0 min | 24.3 min | +24.3 min | +4.3 min |
| Planned prep > 0 | 59 | 12.3 min | 29.6 min | +17.3 min | +8.5 min |

The strongest pattern is not small under-allocation. It is outright missing allocation. Many procedures are scheduled as if no room preparation is needed, even though they actually need substantial prep time.

Examples among high-volume zero-allocation procedures:

- `AV FISTEL ANLÆGGELSE`: **54.5 min** actual prep
- `KHEIRON`: **53.3 min**
- `MESA RAIL TRANSITION`: **43.3 min**
- `SILIKONEOLIEFJERNELSE 25G - LA`: **43.1 min**
- `NYRETRANSPLANTATION`: **40.3 min**

### 3. Three kinds of OR days

| Day type | Days | Mean first-case delay | Mean first-case prep gap | Mean day delay | Mean last-case finish delay |
|---|---:|---:|---:|---:|---:|
| Cascading | 1,096 | 11.8 min | 26.1 min | 34.7 min | 62.0 min |
| Recovery | 997 | 19.6 min | 29.2 min | 3.4 min | -17.1 min |
| One-time shock | 564 | 14.5 min | 26.2 min | 17.7 min | 23.6 min |

The first-case prep gap is large in all three patterns. What changes is not the size of the initial shock, but whether the system absorbs it or lets it propagate through the day.

The notebook also extracts representative real examples for each pattern:

- **Cascading:** `GLO Ø 36 STUE 04` on `2024-02-19`
- **One-time shock:** `GLO Ø 46 STUE 11` on `2025-08-26`
- **Recovery:** `RH DAGKIR D (H)` on `2025-06-30`

### 4. Patient impact

Current patient waiting:

- **70.1%** of cases start late
- **40.9%** start more than 15 minutes late
- **26.0%** start more than 30 minutes late
- **Mean start delay:** `+15.5 min`
- **Median start delay:** `+11.0 min`

If the average prep under-allocation were removed:

- mean start delay would move from `+15.5 min` to `-7.2 min`
- patients would wait **22.8 minutes less on average**

Total impact over two years:

- **14,223 hours** of patient waiting time in late cases
- **14,494 hours** estimated as correctable through better prep allocation
- about **29.0 hours per working day**

The key point is that this does **not** require doing fewer surgeries. The same cases can still be completed; the schedule simply needs to allocate prep time more realistically.

### 5. Model performance

Train/test split:

- **Train (2024):** 19,054 cases
- **Test (2025):** 19,136 cases

Performance on the 2025 test set:

| Approach | MAE | R² |
|---|---:|---:|
| Current schedule | 23.2 min | -0.703 |
| Model prediction | 16.4 min | +0.042 |

Improvement:

- **MAE reduced by 6.8 minutes per case**
- **Mean current prep gap:** `+22.3 min`
- **Mean model prediction gap:** `-1.7 min`

The model also learns an important operational reality that the schedule mostly misses:

| Case type | Actual prep | Predicted prep | Planned prep |
|---|---:|---:|---:|
| Later cases | 16.8 min | 18.8 min | 3.2 min |
| First case of day | 31.3 min | 32.9 min | 4.3 min |

First cases need much more prep because the room starts "cold". The model captures that. The current schedule barely does.

### 6. Example of how model-based allocation could help

The notebook simulates specific OR days by replacing current planned prep with model-predicted prep and then recomputing delays sequentially through the day.

For example:

- **OR room:** `JMC 07`
- **Date:** `2025-04-28`
- **Cases:** 4

Current planned prep was `0` minutes for all four cases, while the model predicted:

- `47.6 min`
- `15.4 min`
- `23.3 min`
- `21.5 min`

Actual prep times were:

- `39 min`
- `31 min`
- `20 min`
- `18 min`

Observed start delays were:

- `+24 min`
- `+40 min`
- `+56 min`
- `+80 min`

Under the notebook's correction logic, the recalculated delays for this day fall to:

- `0.0 min`
- `0.0 min`
- `0.0 min`
- `0.0 min`

This is the clearest operational takeaway: better prep allocation can prevent a late first case from turning into a whole day of avoidable waiting.

## Interpretation

The delays are not primarily evidence that teams spend too long in the OR. They are evidence that the schedule often fails to allocate the prep time the room actually needs before the patient enters.

That changes the intervention:

1. **Immediate fix for common procedures:** use a lookup table based on historical actual prep time.
2. **More flexible fix for broader scheduling:** use a predictive model based on procedure type, staffing, equipment, anesthesia, and position in the day.

Both approaches point in the same direction: allocate prep time realistically up front, reduce unnecessary patient waiting, and reduce the stress placed on doctors and staff who otherwise spend the day trying to catch up to an unrealistic plan.
