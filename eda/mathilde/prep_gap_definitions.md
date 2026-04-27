# How Prep Gap and Surgery Gap Are Calculated

## Timestamps used

All timestamps come from the OR management system. Two types exist for each phase — **planned** (what the scheduler intended) and **actual** (what was recorded by staff).

```
ts_or_prep_planned_start    planned start of OR room preparation
ts_or_prep_start            actual start of OR room preparation

ts_patient_in_or_planned    planned patient entry into OR
ts_patient_in_or            actual patient entry into OR

ts_patient_leaves_or_planned  planned patient exit from OR
ts_patient_leaves_or          actual patient exit from OR
```

---

## Planned prep time

```
planned_prep_min = ts_patient_in_or_planned − ts_or_prep_planned_start
```

How much time the scheduler allocated for OR room preparation before the patient was supposed to arrive.

**Example:** if prep was planned to start at 08:00 and the patient was planned to enter at 08:20, planned prep = 20 minutes.

---

## Actual prep time

```
actual_prep_min = ts_patient_in_or − ts_or_prep_start
```

How long prep actually took — from when staff started preparing the room to when the patient actually entered.

**Example:** if prep actually started at 08:00 and the patient entered at 08:42, actual prep = 42 minutes.

**Data quality note:** 62% of cases have identical values for `ts_or_prep_start` and `ts_or_prep_done` — staff recorded both at the same moment, making the prep start timestamp unreliable for those cases. The analysis excludes these cases, keeping only the 38% where `ts_or_prep_start ≠ ts_or_prep_done`.

---

## Prep gap

```
prep_gap = actual_prep_min − planned_prep_min
```

How many minutes longer prep took than planned. Positive = prep ran over. Negative = prep finished early.

**Example:** planned 20 min, actual 42 min → prep gap = +22 min.

---

## Planned in-OR time (surgery)

```
planned_inor_min = ts_patient_leaves_or_planned − ts_patient_in_or_planned
```

How long the scheduler planned for the patient to be in the OR — from planned entry to planned exit. This covers the full OR window: prep inside the room, anesthesia, surgery, and post-procedure.

---

## Actual in-OR time (surgery)

```
actual_inor_min = ts_patient_leaves_or − ts_patient_in_or
```

How long the patient was actually in the OR.

---

## Surgery gap (in-OR gap)

```
inor_gap = actual_inor_min − planned_inor_min
```

How many minutes longer the full OR stay was than planned. Positive = ran over. Negative = finished early.

---

## What each gap measures

| Gap | What it captures | What it excludes |
|---|---|---|
| `prep_gap` | Whether the room was ready on time | Everything after the patient enters |
| `inor_gap` | Whether the total OR session ran to plan | Room prep before the patient arrives |

These are **independent measures** — a case can have a large prep gap and a small surgery gap (prep ran long, surgery ran to plan) or vice versa. The core finding is that prep gap is systematically larger than surgery gap for 89% of procedures.

---

## What these gaps do NOT include

- **Cascade effects** — if case 2 starts late because case 1 ran over, that inherited delay is not captured in case 2's prep gap. The prep gap only measures case 2's own prep phase.
- **Start delay** — the gap between when the patient was planned to enter the OR and when they actually did. Start delay is a consequence of prep overrun but is computed separately: `start_delay = ts_patient_in_or − ts_patient_in_or_planned`.

---

## Summary in plain language

> *Planned prep gap* is the difference between how long the scheduler thought preparation would take and how long it actually took. *Surgery gap* is the difference between how long the scheduler thought the operation would take and how long it actually took. Both are computed as actual minus planned — positive means it took longer than expected.
