# Preparation Allocation Analysis

This folder contains the analysis for how planned prep time compares with actual prep time, and whether the schedule reflects real case complexity.

## What Is In This Folder

- `planned_prep_allocation.ipynb`: the main notebook for the planning mismatch analysis
- `completed_operations.csv`: source data used by the notebook
- `cancelled_operations.csv`: supplementary source data

## Main Question

Does the schedule allocate prep time in proportion to real complexity, or does it understate the work needed for more complex procedures?

## Delay Logic

The notebook calculates delay as a **step-duration gap**:

- `prep_gap = actual prep duration - planned prep duration`
- `inor_gap = actual in-OR duration - planned in-OR duration`

This compares each step against its own plan. It does **not** automatically chain delays forward from one step to the next.

## What That Means

Because the code uses step-specific planned vs actual durations, it excludes cascading effects when measuring prep and OR delays.

In practice:

- If prep runs late and pushes later milestones back, that lateness is **not** double-counted in the in-OR gap.
- Prep delay and in-OR delay are evaluated separately.
- This makes it easier to identify where the delay originates.

## How To Read The Findings

- A positive prep gap means actual prep took longer than planned.
- A positive in-OR gap means the case stayed in OR longer than planned.
- A negative schedule correlation means the plan is not matching complexity well.

## Open The Notebook

Start with `planned_prep_allocation.ipynb` for the full analysis and presentation-ready charts.

