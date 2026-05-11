# Poster Analysis — OR Scheduling at Rigshospitalet

## The question

Rigshospitalet schedules each surgery in advance: which room, what time, how long. How wrong are those estimates, and what is the root cause?

---

## The short answer

The schedule allocates **zero prep time** for 80.9% of all cases. Those cases start late 81.5% of the time, with a mean delay of +26.7 minutes. When prep time is actually planned, cases start roughly on time or even early.

This is a planning failure, not a performance failure.

---

## The data

- `completed_operations.csv` — 133,158 rows, 120,868 unique cases
- 2 years: 2024-01-01 to 2025-12-31
- 32 surgical specialties, 129 OR rooms

---

## The two windows that matter

### Window 1 — Planned allocation vs. start delay (the main story)

```
planned_prep_min = ts_patient_in_or_planned − ts_or_prep_planned_start
start_delay_min  = ts_patient_in_or         − ts_patient_in_or_planned
```

Both timestamps have >99.5% coverage across all 120k cases. No data quality filter needed.

### Window 2 — Patient-side prep: what prep actually costs (supporting)

```
patient_prep_min = ts_procedure_start − ts_patient_in_or
```

99.3% coverage. Measures the time from when the patient enters the OR to when the surgeon begins — anesthesia, positioning, equipment check. This is what the schedule should be planning for. Only 2.1% of cases have simultaneous-click issues (vs 63.5% for room prep).

All W2 statistics below use a `[0, 240]` minute filter (source: `eda/linus/patient_prep.py`, `PREP_MIN_FILTER`). This removes ~80 extreme outliers from 120,043 cases (W2 raw range: −1431 to +1572 min). Without this filter, R² values are substantially lower (e.g. Spec+Anes lookup drops from 0.576 to 0.466) because outliers inflate total variance.

---

## Finding 1: The schedule allocates almost no prep time

| Planned prep | Cases | Share |
|---|---:|---:|
| 0 min — no allocation | 97,507 | 80.9% |
| 1–10 min | 4,391 | 3.6% |
| 11–20 min | 17,634 | 14.6% |
| 20+ min | 942 | 0.8% |

When prep is allocated, the amounts are small: median 15 min, mean 16 min among the 19% of cases that get any.

---

## Finding 2: Zero allocation directly causes late starts

| Planned prep | Mean start delay | % of cases starting late | % starting 15+ min late |
|---|---:|---:|---:|
| 0 min (no allocation) | +26.7 min | 81.5% | 55.4% |
| 1–10 min | −3.5 min | 42.0% | 24.4% |
| 11–20 min | −2.9 min | 36.5% | 21.3% |
| 20+ min | −8.9 min | 26.2% | 12.6% |

Cases with any planned prep start *early* on average. The relationship is monotonic and strong.

---

## Finding 3: Patient-side prep takes real time — and varies

```
ts_patient_in_or → ts_procedure_start
mean: 32 min  |  median: 27 min  |  p25: 10 min  |  p75: 47 min  |  p90: 67 min
```

The wide spread (10 min at p25, 67 min at p90) reflects real variation driven by case complexity:

| | Cases | Mean patient prep |
|---|---:|---:|
| No anesthesia | 44,929 | 12 min |
| With anesthesia | 75,033 | 44 min |

Whether anesthesia is planned is known before the day of surgery. The schedule ignores it.

---

## Why Mathilde's window was dropped

Mathilde's original analysis used `ts_or_prep_start → ts_patient_in_or` (room prep). This window has a critical data quality problem: 63.5% of cases have identical values for `ts_or_prep_start` and `ts_or_prep_done`, meaning staff clicked both timestamps at the same moment. This makes the start timestamp unreliable for those cases.

After filtering to clean cases, only 39,454 cases remain (32.6% of total). Worse, those cases are not a random sample — they skew toward higher anesthesia rates (79.2% vs 62.4% in the full population) and more complex procedures. Any numbers from this window are biased and not representative of the full picture.

The two windows above (planned allocation + patient-side prep) tell the same story with full coverage and no data quality issues.

---

## Why W2 is the right prediction target (not Mathilde's room prep window)

The natural instinct is to predict room prep time (Mathilde's window: `ts_or_prep_start → ts_patient_in_or`) and use that to set W1. But room prep time **cannot be predicted** from pre-surgery features:

| Target | Lookup table (Spec+Anes) | Gradient Boosting (6 features) |
|---|---:|---:|
| Mathilde — room prep | R² = 0.020 | R² = 0.114 |
| W2 — patient prep | R² = 0.576 | R² = 0.699 |

R² = 0.02 means a lookup table for room prep is useless. Even a gradient boosting model with 200 trees using specialty, anesthesia, staff count, resource count, age, and acute/planned only reaches R² = 0.114 — 89% of the variance remains unexplained. (Room prep R² values use the clean subset with no outlier filter, since applying the [0,240] filter to the already-small clean subset would introduce further selection bias.) Room prep duration depends on things not in the data (which nurse, equipment left from prior case, supply fetching, etc.).

W2 (patient-side prep) is highly predictable. A 64-cell lookup table (Specialty × Anesthesia) already explains 57.6% of the variance. GBM adds a meaningful bump to ~70%.

### Mathilde's LightGBM replication

Mathilde's presentation slides claim a LightGBM model for room prep with R² = 0.187 and MAE = 14.7 min, but her notebook only contains a RandomForest (R² = 0.042, MAE = 16.4). We replicated the LightGBM using her exact data pipeline and got R² = 0.180, MAE = 14.9 — close to her claim but still far below W2's predictability.

### Why room prep doesn't cause the start delay anyway

Staff already know the schedule is broken. On the clean subset (where timestamps are reliable), **64% of room preps start early** (mean 8.5 min before planned). The correlation between Mathilde's room prep window and start delay is r = 0.013 on the clean subset (unfiltered) — effectively zero. Staff absorb room prep variability by starting early.

The start delay is driven by the schedule allocating zero time for in-room setup. W2 (patient prep, mean 32 min) is the largest predictable component of the pre-procedure time.

### The role of each window in the "Analytics to Action" arc

| Window | Role | Coverage |
|---|---|---|
| W1 (planned prep) | **Diagnose**: the schedule allocates no prep | 99.7% |
| W1b (start delay) | **Measure**: quantify the consequence in the hospital's own metric | 99.5% |
| W2 (patient prep) | **Build the fix**: prediction target for the lookup table / model | 99.3% |
| W1b again | **Validate**: simulate whether the new allocation reduces Forsinkelse | 99.5% |

---

## The fix

W2 is both the prediction target and the validation framework. The features needed to predict it already exist in the scheduling system before the day of surgery:

- Specialty (`Speciale`)
- Whether anesthesia is planned (`Anæstesistart` presence)

These two features alone yield a 64-cell lookup table with R² = 0.576. Additional features provide diminishing returns:

| Features | Method | R² | Notes |
|---|---|---:|---|
| Anesthesia only | Lookup | 0.386 | 2 groups |
| Specialty only | Lookup | 0.463 | 32 groups |
| Specialty + Anesthesia | Lookup | 0.576 | 64 groups |
| Specialty + Anes + Age + Acute | OLS | 0.583 | |
| Spec + Anes + staff/resource counts | OLS | 0.626 | |
| Spec + Anes + Age + 50 PCA components | OLS | 0.689 | PCA on 214 binary staff/resource cols |
| 6 features | Gradient boosting | 0.699 | |

### OLS and PCA analysis

OLS regression with the same features as the lookup table (specialty + anesthesia) gets R² = 0.563 — slightly *below* the lookup table (0.576). The lookup's group means capture the full non-linear interaction without assuming linearity. OLS with explicit interaction terms (specialty × anesthesia) gets 0.571 — still below.

Adding staff and resource counts improves OLS to 0.626. PCA on all 214 binary staff/resource columns does better: 50 PCA components added to OLS reach R² = 0.689, nearly matching GBM (0.699). The PCA components capture *which specific equipment and staff* are involved, not just how many — e.g., a cardiac setup vs a simple scope.

However, PCA largely rediscovers specialty: 20 PCA components predict specialty with 71% accuracy. The additional value comes from within-specialty variation (complex vs simple cases within the same department using different equipment).

The R² ceiling appears to be ~0.70 regardless of method (OLS+PCA ≈ GBM). The remaining 30% of variance is likely irreducible — driven by factors not in the data: which specific anesthesiologist, patient cooperation, equipment availability, prior case state.

### Simulated impact of the lookup table

Applying the Specialty × Anesthesia lookup as the new planned prep allocation. The simulation holds actual events fixed and recomputes Forsinkelse under the new plan — the standard counterfactual methodology in OR scheduling research (Dexter & Macario). Actual durations are exogenous: they depend on patient, procedure, and team, not the schedule.

`new_delay = start_delay − (lookup_alloc − planned_prep)`

| Metric | Current schedule | With lookup table |
|---|---:|---:|
| Mean start delay | +21.0 min | −7.9 min |
| % starting late | 73.1% | 38.5% |
| % starting 15+ min late | 49.0% | 30.2% |
| Late starts eliminated | — | ~41,400 fewer cases |

The mean going negative (−7.9 min) means cases would on average show as "early" — the schedule now has buffer instead of deficit. This is the intended direction: the current system is systematically behind, and the fix flips it to systematically having headroom.

The remaining 38.5% late starts reflect delay sources beyond W2 — prior case overruns, patient transport, equipment issues. These require different interventions. The lookup specifically fixes the systematic bias from zero prep allocation, which is the largest single contributor.

**Note on an alternative metric:** Computing `actual_W2 − lookup_mean` (the prediction residual) gives the tighter-looking numbers of 45.7% late and 13.1% 15+ min late. However, this centers at zero by construction and measures the lookup's prediction accuracy, not the operational impact on Forsinkelse. It answers "what fraction of cases have W2 longer than the group mean?" — a statistical property, not a schedule simulation. We use the counterfactual simulation above because it answers the actual question: what would happen to the hospital's delay metric if the schedule changed.

The goal is not to do fewer surgeries. The same cases run; the schedule just needs to allocate the time the OR actually needs before the procedure starts.

### Why we recommend the lookup table over a ML model

The gradient boosting model (R² = 0.699) outperforms the lookup table (R² = 0.576) statistically, but we recommend the lookup table as the immediate intervention for three reasons:

**The practical gap is small.** The lookup table already flips mean delay from +21 min to −8 min and halves the late-start rate from 73% to 39%. The ML model would shave more off the edges, but the bulk of the win is already captured by the table. The scheduling system currently allocates zero minutes for 81% of cases — going from zero to a lookup table captures the vast majority of the improvement.

**Adoption.** A lookup table is a 64-cell grid that can be printed and taped to a wall. A scheduler can glance at it: cardiothoracic + anesthesia = 52 min buffer. Done. An ML model requires infrastructure — someone has to maintain it, feed it live data, handle edge cases, and explain why it produced a particular number. Rigshospitalet does not have that pipeline today, and building it introduces delay and risk to an otherwise straightforward fix.

**Trust.** When you tell a head nurse "we need 44 minutes for anesthesia cases in your specialty because that's the historical average," they can verify it against their own experience. When you tell them "the model says 47.3 minutes," they ask why, and the answer is a black box. For a first intervention in a system that has never allocated prep time at all, explainability matters more than the last few percentage points of R².

The ML model should be positioned as a **future refinement** — once the hospital has adopted the lookup table and wants to squeeze out more accuracy, a model can be layered on top. But the first step is getting from zero to a reasonable default, and the lookup table does that with no infrastructure requirements.

---

## What Linus's analysis adds

Linus's work shows that the start delay caused by missing prep time does not stay isolated — it cascades through the day:

- The delay **amplifies**: zero-prep cases start +26.7 min late and end +30.7 min overrun
- OR days where the first case starts late see mean delays of 34.7 min by the last case (cascading pattern)
- OR days where prep is better managed recover to near-zero delay by mid-day

The prep allocation failure is also not uniform across specialties. Some specialties (e.g. Øjenkirurgi: 100% zero planned prep, mean start delay +42.7 min) are systematically worse than others.

This is **not an acute-case artifact**: 84% of *planned* cases also get zero prep allocation. Acute cases actually have a lower zero-prep rate (69%).

---

## Data quality: an actionable recommendation

### The problem

Two timestamp pairs suffer from widespread simultaneous-click registration:

| Timestamp pair | Simultaneous click rate | Usable cases |
|---|---:|---:|
| Room prep (start → done) | 63.5% | 39,454 (32.6%) |
| Cleaning (start → done) | 79.7% | 10,195 (8.4%) |
| Patient prep (W2: patient in → procedure start) | 2.1% | 117,506 (97.2%) |

When staff click "start" and "done" at the same moment, both timestamps are lost. The remaining clean data is biased toward complex cases (79.2% anesthesia rate in clean room prep data vs 62.4% in the full population).

### Why this matters

We cannot tell whether room prep time is inherently unpredictable or whether the data is simply too broken to reveal the pattern. On the biased 32% clean subset, the best model reaches R² = 0.13. With clean timestamps for all 120k cases, that number might stay at 0.13 (room prep is genuinely driven by unobservable factors like which nurse, supply availability, prior case leftovers) — or it might increase substantially, meaning the signal was there but hidden by garbage data.

The same applies to cleaning time. With 79.7% simultaneous clicks, cleaning duration is completely unanalyzable.

### The fix

Add a validation rule in the OR management system: `Stue klargjort` must be recorded at least N minutes after `Stue klargøring start` (and similarly for cleaning). This is a software change, not a workflow change — staff already perform the prep, they just don't record the timestamps separately.

### What the hospital would gain

The ability to optimize the **full** pre-surgery timeline, not just the patient-side half. Room prep averages ~25 min on the clean subset. If it turns out to be predictable with representative data, the same lookup-table approach could be applied to room prep allocation, further reducing delays. Combined with the W2 fix, this would cover the entire window from room open to first cut.

---

## What we actually showed vs. what we didn't

### What the analysis shows

The schedule allocates zero prep time for 81% of cases. Those cases register as +27 min late on the hospital's own delay metric (Forsinkelse). A lookup table (specialty × anesthesia) makes the plan realistic by allocating prep time that matches historical averages. Under this new plan, the same actual events produce a smaller delay metric: mean +21 → −8 min, late starts 73% → 39%.

This is a **metric fix**, not an operational fix. The "41,400 fewer late starts" are cases that flip from "late" to "on time" because the plan moved — not because anything changed in the OR. The actual patient arrivals, prep durations, and surgery times are identical. The simulation literally subtracts the lookup table's prep time from each case's delay — nothing else is modeled.

### Presentation caveat: the Gantt chart

The before/after Gantt chart (poster panel 3) is technically correct — the actual bars (dark) are identical in both panels, showing that reality doesn't change. But a casual reader may interpret it as "the fix makes surgeries start on time." It doesn't — it makes the *plan* match reality. The delays shrink because the reference point (planned surgery start) shifts right, not because the patient arrives earlier. When presenting, be prepared to explain this distinction.

### What we cannot see

We don't know **why** patients enter the OR late. The delay could be caused by:

- Room prep running long (equipment, cleaning, supply fetching)
- Patient not transported from the ward in time
- Prior case overrunning
- Anesthesia team unavailable
- Any combination of these

The timestamp window that would answer this — Mathilde's room prep window (`ts_or_prep_start` → `ts_patient_in_or`) — has 63.5% simultaneous clicks, making it unusable for the full population. On the biased 33% clean subset, room prep is unpredictable (R² = 0.02), but we cannot tell if that's because room prep is genuinely random or because the data is too broken to reveal the pattern.

### The data quality recommendation closes this gap

If the hospital adds a validation rule enforcing a minimum time between "start" and "done" clicks for room prep (and cleaning), we would have clean timestamps for all 120k cases. This would allow:

1. Identifying the actual causal chain behind patient delays
2. Testing whether room prep is predictable with representative (unbiased) data
3. Building a second lookup table for room prep allocation, covering the full pre-surgery timeline

This is a software change, not a workflow change — staff already perform the prep, they just don't record the timestamps separately. It is also a direct application of data collection design principles from the course: the question you can answer is bounded by the data you choose to collect.

### Limitation: our lookup table only covers half the pre-surgery timeline

The current fix allocates time for W2 (patient-side prep: patient enters OR → procedure starts). It does not cover room prep (room opens → patient enters), which is the upstream stage. A complete schedule allocation would be:

```
total allocation = room prep + patient prep (W2)
```

With clean room prep timestamps, the same lookup-table approach could be applied to room prep, and both could be combined to cover the full window from "room opens" to "first cut." Currently we can only plan for the patient-side half because the room-prep half's data is broken.

### Follow-up: does fixing the plan fix the actual delays?

Our simulation shows the metric improves, but the actual OR events are held fixed. The open question is: if the hospital implemented realistic prep allocation, would actual patient arrivals and start times improve? Plausible mechanisms:

- Schedulers space cases with realistic gaps, reducing cascading pressure
- Staff stop working against an impossible plan
- Patients get called from the ward at the right time
- The delay metric stops being dominated by planning error, letting management focus on genuine operational issues

This would require a before/after study: implement the lookup table, run for a few months, compare actual delays to the historical baseline. The evaluation infrastructure is already in place — the delay metric (Forsinkelse) has 99.5% coverage and clean data.

### What the lookup table actually gives the hospital

The lookup table's value is **making the schedule tell the truth**. This is modest but has concrete consequences:

1. **The delay metric becomes actionable.** Right now "73% late" is noise — it mostly measures a planning error, not OR performance. With realistic allocation, a case showing up as "late" actually means something went wrong operationally. Management can investigate those cases instead of shrugging at a number that's always bad.

2. **Case sequencing gets realistic.** If the scheduler knows each case needs 34 min of prep, they can fit the right number of cases in a day. Currently they may be scheduling cases assuming zero prep, when realistically fewer fit.

3. **Patient communication.** You can tell a patient "your surgery starts at 9:30" instead of "9:00" and be right.

None of these are guaranteed outcomes — they depend on the hospital actually using the allocation to change how they schedule. The lookup table is a tool, not a fix by itself.

The bigger value is probably the **insight** rather than the specific 64-cell table: showing the hospital that their scheduling system has a structural blind spot where 81% of cases are planned with zero prep time, and that this single planning failure accounts for most of their delay metric.

---

## Numbers to quote in the poster

### The problem

| Metric | Value |
|---|---|
| Cases with zero planned prep | 80.9% (97,507 / 120,474) |
| Mean start delay, zero-prep cases | +26.7 min |
| % starting late, zero-prep cases | 81.5% |
| Mean start delay, any planned prep | −3.3 min (starts early) |
| Mean start delay, 20+ min planned | −8.9 min (starts early) |
| Planned (non-acute) cases with zero prep | 84.0% (not an acute-case artifact) |
| Delay amplification | +26.7 start delay → +30.7 overrun |
| Total unique cases | 120,868 |
| Date range | 2024-01-01 – 2025-12-31 |

### The fix

| Metric | Value |
|---|---|
| Mean patient-side prep (W2) | 32 min |
| W2 with anesthesia | 44 min (n=75,033) |
| W2 without anesthesia | 12 min (n=44,929) |
| Lookup table R² (Specialty × Anesthesia) | 0.576 (64 groups) |
| ML model R² (gradient boosting, 6 features) | 0.699 |
| Simulated mean delay with lookup | −7.9 min (from +21.0) |
| Simulated % late with lookup | 38.5% (from 73.1%) |
| Simulated % 15+ min late with lookup | 30.2% (from 49.0%) |
| Late starts eliminated | ~41,400 fewer cases |

### Why not predict room prep instead

| Metric | Value |
|---|---|
| Room prep R² (lookup table, clean, unfiltered) | 0.020 — unpredictable |
| Room prep R² (GBM, clean, unfiltered) | 0.114 — still bad |
| Room prep R² (Mathilde's LightGBM) | 0.180 — still far below W2 |
| Room prep correlation with start delay | r = 0.013 — effectively zero |
| Staff starting room prep early (clean subset) | 64% of cases (mean 8.5 min early) |

### Data quality recommendation

| Metric | Value |
|---|---|
| Room prep simultaneous-click rate | 63.5% — blocks analysis |
| Cleaning simultaneous-click rate | 79.7% — completely unusable |
| W2 simultaneous-click rate | 2.1% — no issue |
| Clean room prep subset bias | 79.2% anesthesia rate vs 62.4% population |
| Recommendation | Enforce minimum time between start/done timestamps |

### Hospital's own metrics

| Metric | Value |
|---|---|
| Forsinkelse (minutter) = our W1b (start delay) | correlation = 1.0000 |
| Overskredet (minutter) = our finish overrun | correlation = 1.0000 |
