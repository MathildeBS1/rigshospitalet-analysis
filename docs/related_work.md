# Related Work

## Hara et al. (2024) — the closest comparison

**Paper:** Hara K et al. "Development of an estimation formula for preparation time of anesthesia induction and surgery accounting for clinical department factors." *Scientific Reports* 14:25185, 2024. Open access: PMC11502697.

**What they did:** Predicted patient-in-room to incision time (our W2) using OLS regression at Nagasaki Medical Center (Japan). 12,528 cases, 15 departments, 6 anesthesia types, 9 procedure-level binary flags (catheter types, navigation, endoscope). R² = 0.801.

**What they didn't do:** No diagnosis of the scheduling system. No simulation of impact on delays. No implementation recommendation. Their paper is "we can predict this accurately" — it stops at prediction validation.

### Comparison

| | Hara et al. | Our analysis |
|---|---|---|
| Target variable | Patient enters OR → incision | Patient enters OR → procedure start (same) |
| Method | OLS regression | Lookup table (+ GBM comparison) |
| Key features | 15 depts + 6 anesthesia types + 9 procedure flags | 32 specialties × anesthesia yes/no |
| R² | 0.801 | 0.576 (lookup), 0.699 (GBM) |
| N cases | 12,528 | 120,868 |
| Scheduling diagnosis | None | 81% get zero prep allocated |
| Impact simulation | None | Counterfactual: +21 → −8 min, late starts 73% → 39% |
| Recommendation | "Use the formula" | Lookup table over ML; fix data collection |

### Why their R² is higher

1. **Finer anesthesia coding** — 6 types (general, spinal, local, IV sedation, epidural, nerve block) vs our binary yes/no
2. **Procedure-level features** — arterial line, central line, epidural catheter, navigation system, etc. capture within-specialty variance
3. **Smaller, more homogeneous hospital** — 12.5k cases, 15 departments vs 121k cases, 32 specialties

### Why we should mention it in the poster presentation

- Validates our approach: independent group, different hospital, different country, same conclusion — specialty + anesthesia predicts pre-incision time
- Shows where our model could improve: finer anesthesia granularity and procedure flags would close the R² gap
- Highlights what we add beyond their work: the full analytics-to-action arc (diagnose → measure → fix → simulate → recommend)

## Other relevant work

**Dexter et al. (2007)** — "Identification of systematic underestimation (bias) of case durations during case scheduling." Established the term for what we found: persistent underestimation caused by slight bias across many cases, not poor decisions on outlier cases.

**Cureus (2021), PMC7854319** — "The Planning Fallacy in the Orthopedic Operating Room." Applied Kahneman & Tversky's planning fallacy to surgical scheduling. Surgeons exhibit "coordination neglect" — they estimate knife-time but ignore non-operative steps.

**Dexter (2022)** — Argued that unbiased predictions of OR times increase labor productivity even with unchanged staffing. Our exact argument: the fix doesn't change operations, it makes the plan unbiased, which makes the metric meaningful.
