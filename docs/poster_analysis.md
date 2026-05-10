# Poster Analysis — OR Scheduling at Rigshospitalet

## The question

Rigshospitalet schedules each surgery in advance: which room, what time, how long. How wrong are those estimates, and what is the root cause?

---

## The short answer

The schedule allocates **zero prep time** for 80.9% of all cases. Those cases start late 82.8% of the time, with a mean delay of +27.9 minutes. When prep time is actually planned, cases start roughly on time or even early.

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

Both timestamps have >99.6% coverage across all 120k cases. No data quality filter needed.

### Window 2 — Patient-side prep: what prep actually costs (supporting)

```
patient_prep_min = ts_procedure_start − ts_patient_in_or
```

99.3% coverage. Measures the time from when the patient enters the OR to when the surgeon begins — anesthesia, positioning, equipment check. This is what the schedule should be planning for.

---

## Finding 1: The schedule allocates almost no prep time

| Planned prep | Cases | Share |
|---|---:|---:|
| 0 min — no allocation | 95,450 | 80.9% |
| 1–10 min | 3,886 | 3.3% |
| 11–20 min | 16,524 | 14.0% |
| 20+ min | 889 | 0.8% |

When prep is allocated, the amounts are small: median 15 min, mean 16 min among the 19% of cases that get any.

---

## Finding 2: Zero allocation directly causes late starts

| Planned prep | Mean start delay | % of cases starting late | % starting 15+ min late |
|---|---:|---:|---:|
| 0 min (no allocation) | +27.9 min | 82.8% | 56.2% |
| 1–10 min | +5.0 min | 46.5% | 26.7% |
| 11–20 min | +3.0 min | 38.4% | 22.2% |
| 20+ min | −4.8 min | 27.3% | 12.9% |

Cases with 20+ min planned prep start *early* on average. The relationship is monotonic and strong.

---

## Finding 3: Patient-side prep takes real time — and varies

```
ts_patient_in_or → ts_procedure_start
mean: 32 min  |  median: 27 min  |  p25: 10 min  |  p75: 47 min  |  p90: 67 min
```

The wide spread (10 min at p25, 67 min at p90) reflects real variation driven by case complexity:

| | Cases | Mean patient prep |
|---|---:|---:|
| No anesthesia | ~44k | ~12 min |
| With anesthesia | ~75k | ~44 min |

Whether anesthesia is planned is known before the day of surgery. The schedule ignores it.

---

## Why Mathilde's window was dropped

Mathilde's original analysis used `ts_or_prep_start → ts_patient_in_or` (room prep). This window has a critical data quality problem: 63.5% of cases have identical values for `ts_or_prep_start` and `ts_or_prep_done`, meaning staff clicked both timestamps at the same moment. This makes the start timestamp unreliable for those cases.

After filtering to clean cases, only 39,227 cases remain (32.5% of total). Worse, those cases are not a random sample — they skew toward higher anesthesia rates (76.8% vs 51.7%) and more complex procedures. Any numbers from this window are biased and not representative of the full picture.

The two windows above (planned allocation + patient-side prep) tell the same story with full coverage and no data quality issues.

---

## The fix

The information needed to allocate prep time correctly already exists in the scheduling system before the day of surgery:

- Procedure type
- Whether anesthesia is planned
- Staff count
- Equipment count
- Case position in the day (first cases need more — the room starts cold)

A simple lookup table by procedure type would already close most of the gap. A model using the features above would do better still.

The goal is not to do fewer surgeries. The same cases run; the schedule just needs to allocate the time the room actually needs before the patient enters.

---

## What Linus's analysis adds

Linus's work shows that the start delay caused by missing prep time does not stay isolated — it cascades through the day:

- OR days where the first case starts late see mean delays of 34.7 min by the last case (cascading pattern)
- OR days where prep is better managed recover to near-zero delay by mid-day

The prep allocation failure is also not uniform across specialties. Some specialties (e.g. Øjenkirurgi: 100% zero planned prep, mean start delay +42.7 min) are systematically worse than others.

The turnaround analysis shows that between-case idle time averages ~25 min, and a meaningful fraction of this is dead time before cleaning starts or after the room is ready — further compounding the scheduling inefficiency.

---

## Numbers to quote in the poster

| Metric | Value |
|---|---|
| Cases with zero planned prep | 80.9% (95,450 / 120,474) |
| Mean start delay, zero-prep cases | +27.9 min |
| % starting late, zero-prep cases | 82.8% |
| Mean start delay, 20+ min planned | −4.8 min (starts early) |
| Mean patient-side prep time | 32 min |
| Mean patient-side prep with anesthesia | ~44 min |
| Mean patient-side prep without anesthesia | ~12 min |
| Total unique cases | 120,868 |
| Date range | 2024-01-01 – 2025-12-31 |
