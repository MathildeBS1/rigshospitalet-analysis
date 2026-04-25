# The Scheduling Gap: Why Prep Overruns Are a Planning Problem, Not a Performance Problem

## The finding in one table

| Factor | Actually affects prep time (r) | Schedule accounts for it (r) |
|---|---|---|
| Staff count | +0.49 | −0.08 |
| Equipment count | +0.27 | −0.16 |

## What the numbers mean

The r values are correlation coefficients. They measure how strongly two things move together, from −1 (perfect inverse) through 0 (no relationship) to +1 (perfect match).

These values are calculated on procedures with `n >= 50`.

### Left column: what reality looks like

When we measure how long prep *actually takes* across departments, we find that staff count matters. Departments averaging 7–8 staff per case genuinely need more prep time than departments with 3–4 — coordinating more people, confirming more roles, getting everyone briefed and positioned. The correlation of r = +0.49 means staff count explains a substantial share of the variation in actual prep duration. Equipment (r = +0.27) adds to this, but more weakly: more devices to stage, calibrate, and position means more time before the patient is ready.

These numbers describe the operational reality of running an OR.

### Right column: what the schedule assumes

When we measure how much prep time the *schedule allocates*, the correlations collapse. Staff count at r = −0.08 is essentially zero — the schedule gives nearly the same prep window whether a case needs 3 people or 8. Equipment at r = −0.16 is slightly *negative*, meaning equipment-heavy cases actually get marginally less planned prep time, which is the opposite of what they need.

The schedule is effectively blind to complexity.

### The gap between the columns is the root cause

Reality says: more staff and equipment → more prep time needed.
The schedule says: doesn't matter, everyone gets roughly the same window.

That mismatch shows up every day as prep overruns. Departments with complex, high-staff cases systematically exceed their planned prep time — not because they are slow, but because the plan doesn't reflect what it actually takes to get a complex case started.

## Why this matters

- 79% of procedures with n >= 50 have a larger prep gap than in-OR gap. Surgeons run close to plan once they start — the system loses time getting them started.
- The prep gap correlates with department complexity, but the schedule does not adjust for it.
- Staff is the clearest missed input in the plan; equipment is weaker but still misallocated.

The delays are not a performance problem. They are a planning problem.

## Interpretation note

The updated numbers are even worse than simple under-capture: for the filtered procedure set, the schedule signal is inverse for both staff and equipment. That means the plan is not just too flat — it is moving in the wrong direction.

## Recommendation

Planned prep time should be adjusted based on case complexity — at minimum by department, ideally by procedure. The data already contains the inputs needed: staff count and equipment requirements are known before the day of surgery. Feeding these into the scheduling algorithm would close the gap between what the plan assumes and what the OR floor actually needs.
