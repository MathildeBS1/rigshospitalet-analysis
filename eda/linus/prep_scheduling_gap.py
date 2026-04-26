"""
EDA 6: Prep Scheduling Gap (rewrite of Mathilde's analysis)

Faithful port of eda/mathilde/prep-complexity-gap/planned_prep_allocation.ipynb
to Polars + the shared data loader.

Mathilde's windows:
  actual_prep_min  = ts_or_prep_start      → ts_patient_in_or
  planned_prep_min = ts_or_prep_planned_start → ts_patient_in_or_planned
  actual_inor_min  = ts_patient_in_or      → ts_patient_leaves_or
  planned_inor_min = ts_patient_in_or_planned → ts_patient_leaves_or_planned

Data quality note: ts_or_prep_start has 62% same-timestamp entries with
ts_or_prep_done, meaning actual_prep_min is unreliable for ~62% of cases —
it collapses to the post-room-ready gap rather than the full prep phase.
Correlations and gaps are directionally valid but magnitudes are understated.
See docs/data/prep-time-definitions.md for the cleaner alternative window.
"""

import polars as pl

from data.loader import load_completed
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CASES_PER_PROCEDURE = 50
GAP_CLIP = 300  # minutes — matches Mathilde's abs() < 300 filter


def run(specialty: str | None = None) -> None:
    logger.info("Loading completed operations...")
    df = load_completed()

    if specialty:
        df = df.filter(pl.col("specialty") == specialty)
        logger.info(f"Filtered to specialty: {specialty}")

    cases = df.unique(subset=["case_id"], keep="first")

    staff_cols = [c for c in cases.columns if c.startswith("staff_")]
    resource_cols = [c for c in cases.columns if c.startswith("resource_")]

    cases = cases.with_columns([
        (pl.col("ts_or_prep_start") - pl.col("ts_or_prep_planned_start"))
        .dt.total_minutes().alias("_unused"),  # kept for symmetry

        (pl.col("ts_patient_in_or") - pl.col("ts_or_prep_start"))
        .dt.total_minutes().alias("actual_prep_min"),

        (pl.col("ts_patient_in_or_planned") - pl.col("ts_or_prep_planned_start"))
        .dt.total_minutes().alias("planned_prep_min"),

        (pl.col("ts_patient_leaves_or") - pl.col("ts_patient_in_or"))
        .dt.total_minutes().alias("actual_inor_min"),

        (pl.col("ts_patient_leaves_or_planned") - pl.col("ts_patient_in_or_planned"))
        .dt.total_minutes().alias("planned_inor_min"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in staff_cols])
        .alias("staff_count"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in resource_cols])
        .alias("resource_count"),
    ]).with_columns([
        (pl.col("actual_prep_min") - pl.col("planned_prep_min")).alias("prep_gap"),
        (pl.col("actual_inor_min") - pl.col("planned_inor_min")).alias("inor_gap"),
    ]).drop("_unused")

    valid = cases.filter(
        pl.col("prep_gap").is_not_null(),
        pl.col("inor_gap").is_not_null(),
        pl.col("prep_gap").abs() < GAP_CLIP,
        pl.col("inor_gap").abs() < GAP_CLIP,
    )
    logger.info(f"Cases in analysis set: {valid.shape[0]:,}")

    # ── 1. Prep vs in-OR gap (hospital level) ───────────────────────────────
    logger.info("\n── Hospital-level gap: prep vs in-OR ──")
    logger.info(f"  Mean prep gap:   {valid['prep_gap'].mean():+.1f} min")
    logger.info(f"  Mean in-OR gap:  {valid['inor_gap'].mean():+.1f} min")

    # ── 2. Procedure-level (n >= 50) — replicates Mathilde's main chart ─────
    logger.info(f"\n── Procedure-level gaps (n >= {MIN_CASES_PER_PROCEDURE}) ──")
    proc = (
        valid
        .filter(pl.col("procedure_text_id").is_not_null())
        .group_by("procedure_text_id")
        .agg(
            pl.len().alias("n"),
            pl.col("prep_gap").mean().alias("prep_gap_mean"),
            pl.col("inor_gap").mean().alias("inor_gap_mean"),
            pl.col("planned_prep_min").mean().alias("planned_prep_mean"),
            pl.col("staff_count").mean().alias("mean_staff"),
            pl.col("resource_count").mean().alias("mean_resources"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_PROCEDURE)
    )
    logger.info(f"Procedures with n >= {MIN_CASES_PER_PROCEDURE}: {proc.shape[0]}")

    pct_prep_worse = (proc["prep_gap_mean"] > proc["inor_gap_mean"]).mean() * 100
    logger.info(f"Share where prep gap > in-OR gap: {pct_prep_worse:.1f}%")
    logger.info(f"Mean prep gap across filtered procedures:   {proc['prep_gap_mean'].mean():+.1f} min")
    logger.info(f"Mean in-OR gap across filtered procedures:  {proc['inor_gap_mean'].mean():+.1f} min")

    # ── 3. Complexity signal vs scheduling capture ───────────────────────────
    logger.info("\n── Complexity signal: actual effect vs scheduling capture ──")

    r_staff_actual   = proc.select(pl.corr("mean_staff",     "prep_gap_mean")).item()
    r_resource_actual = proc.select(pl.corr("mean_resources", "prep_gap_mean")).item()
    r_staff_sched    = proc.select(pl.corr("mean_staff",     "planned_prep_mean")).item()
    r_resource_sched = proc.select(pl.corr("mean_resources", "planned_prep_mean")).item()

    logger.info("Staff count:")
    logger.info(f"  actual effect on prep gap:    r = {r_staff_actual:+.2f}")
    logger.info(f"  schedule accounts for it:     r = {r_staff_sched:+.2f}")
    logger.info("Resource count:")
    logger.info(f"  actual effect on prep gap:    r = {r_resource_actual:+.2f}")
    logger.info(f"  schedule accounts for it:     r = {r_resource_sched:+.2f}")

    # ── 4. Top over/under-scheduled procedures ───────────────────────────────
    logger.info("\n── Top 10 most over-scheduled procedures (prep runs furthest over) ──")
    print(
        proc.sort("prep_gap_mean", descending=True)
        .head(10)
        .select(["procedure_text_id", "n", "prep_gap_mean", "inor_gap_mean", "mean_staff", "mean_resources"])
        .with_columns([
            pl.col("prep_gap_mean").round(1),
            pl.col("inor_gap_mean").round(1),
            pl.col("mean_staff").round(1),
            pl.col("mean_resources").round(1),
        ])
    )


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
