# Key Terms

## What we found

**Systematic underestimation bias** — the schedule consistently underestimates how long cases take by omitting prep time entirely. Not a few outlier cases — 81% of all cases. (Dexter et al., 2007)

**Planning fallacy / coordination neglect** — surgeons estimate their own knife-time but ignore anesthesia induction, positioning, and equipment checks. The schedule captures surgical time but omits everything before first incision. (Kahneman & Tversky; applied to OR scheduling in PMC7854319, 2021)

**Pre-incision time** — the time from patient entering the OR to first cut. Also called "anesthesia-controlled time" or "patient-in-room to incision time." This is what the schedule sets to zero. Literature reports 21–49 min depending on specialty and anesthesia type.

## What we built

**Case-mix adjusted time allocation** — a lookup table that predicts prep time based on case characteristics (specialty × anesthesia). "Case mix" is the standard term for the combination of factors that determine expected durations. (Ito et al., Scientific Reports, 2024 — did nearly the same thing, R² = 0.801)

**Calibrated scheduling** — moving from a biased plan (systematically wrong) to one that matches reality. The schedule becomes "unbiased" in the statistical sense: predictions center on actual durations. (Dexter, 2022)

## What we simulated

**Retrospective what-if analysis** — replaying historical events under a different allocation rule. Also called "trace-driven simulation." We held actual events fixed and recomputed the delay metric with the new plan. This is deterministic (no stochastic modeling), which makes it simpler and more defensible than a full discrete-event simulation.

## What we couldn't do

**Temporal uncertainty / retrospective documentation** — 64% of room prep timestamps are simultaneous clicks (staff batch-enter events after the fact). This is a known problem in clinical databases. Without reliable timestamps, we cannot identify the causal chain behind delays. (PMC9433547, 2022)

## The broader framework

**The Surgical Scheduling Problem** — the overarching field in operations research. Key authors: Franklin Dexter (Iowa), Alex Macario (Stanford). Our work fits within "within-day scheduling" — how to allocate time to individual cases within an OR block.
