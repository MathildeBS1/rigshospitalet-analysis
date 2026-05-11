# Poster Structure

## Title

**Why Surgeries Start Late: A Scheduling Fix for Rigshospitalet**

---

## Panel 1 — The Problem

**"The schedule allocates zero prep time for 81% of surgeries"**

Rigshospitalet's OR schedule sets planned prep time to zero for 80.9% of cases (97,507 / 120,474). Those cases start +26.7 min late on average, with 81.5% starting after their planned time. When prep time *is* allocated, cases start early.

This is a planning failure, not a performance failure. The schedule pretends that the time between a patient entering the OR and the first incision — anesthesia, positioning, equipment checks — takes zero minutes. It doesn't.

**Chart**: Diverging horizontal bar chart. Four prep-allocation buckets (0, 1–10, 11–20, 20+ min) on the y-axis, mean start delay on x-axis. The zero-prep bar extends far right (+26.7 min). The other three extend left (early). Case counts on the right show the 81/19 asymmetry.

---

## Panel 2 — The Fix

**"A 64-cell lookup table predicts what the schedule ignores"**

Patient-side prep (W2: patient enters OR → procedure starts) takes real, predictable time: mean 44 min with anesthesia, 12 min without. Both specialty and anesthesia status are known before the day of surgery. A lookup table on just these two features explains 57.6% of W2 variance (R² = 0.576, 64 groups).

We recommend the lookup table over a machine learning model (R² = 0.699) because the practical gap is small, it requires no infrastructure, and clinical staff can verify it against their own experience.

**Chart**: Heatmap of the 64-cell lookup table — specialty (rows) × anesthesia yes/no (columns), colored by mean W2 minutes. This IS the deliverable: a grid a scheduler can read directly.

---

## Panel 3 — The Impact

**"Simulated: late starts halved, 41,400 fewer delays"**

Counterfactual simulation holding actual events fixed, recomputing Forsinkelse (the hospital's own delay metric) under the new allocation:

| Metric | Current | With lookup |
|---|---|---|
| Mean start delay | +21.0 min | −7.9 min |
| % starting late | 73.1% | 38.5% |
| Late starts eliminated | — | ~41,400 |

The mean going negative means the schedule flips from systematic deficit to systematic buffer. The remaining 38.5% late starts reflect delay sources beyond prep allocation (prior case overruns, transport, equipment) — different problems requiring different interventions.

**Chart**: Before/after paired bars or overlaid distributions showing the shift in start delay under the current vs. lookup schedule.

---

## Data

- 133,158 rows, 120,868 unique cases, 2024–2025
- 32 specialties, 129 OR rooms
- W2 outlier filter: [0, 240] min (removes ~80 extreme values)
- Problem chart uses all data (no outlier filter)

## Word budget

Target: ~400 of 450 words. Leave room for axis labels and source line.
