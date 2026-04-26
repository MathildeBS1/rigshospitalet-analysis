"""
EDA 7: In-OR Time Decomposition

Breaks the actual in-OR time into three clean phases:
  1. patient_prep_min   ts_patient_in_or      → ts_procedure_start  (get patient ready)
  2. procedure_min      ts_procedure_start    → ts_procedure_end    (actual surgery)
  3. post_procedure_min ts_procedure_end      → ts_patient_leaves_or (wind down)

Compares the sum against the planned in-OR slot to show where time goes
and what the schedule gets wrong — without touching any garbage timestamps.

All four timestamps used have >99% coverage and no same-timestamp problem.
"""

import polars as pl

from data.loader import load_completed
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_CASES_PER_PROCEDURE = 50


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
        (pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
        .dt.total_minutes().alias("patient_prep_min"),

        (pl.col("ts_procedure_end") - pl.col("ts_procedure_start"))
        .dt.total_minutes().alias("procedure_min"),

        (pl.col("ts_patient_leaves_or") - pl.col("ts_procedure_end"))
        .dt.total_minutes().alias("post_procedure_min"),

        (pl.col("ts_patient_leaves_or") - pl.col("ts_patient_in_or"))
        .dt.total_minutes().alias("actual_inor_min"),

        (pl.col("ts_patient_leaves_or_planned") - pl.col("ts_patient_in_or_planned"))
        .dt.total_minutes().alias("planned_inor_min"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in staff_cols])
        .alias("staff_count"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in resource_cols])
        .alias("resource_count"),
    ])

    valid = cases.filter(
        pl.col("patient_prep_min").is_between(0, 240),
        pl.col("procedure_min").is_between(0, 600),
        pl.col("post_procedure_min").is_between(0, 240),
        pl.col("planned_inor_min").is_between(0, 600),
    )
    logger.info(f"Cases with all four clean timestamps: {valid.shape[0]:,}")

    # ── 1. Mean breakdown of actual in-OR time ───────────────────────────────
    logger.info("\n── Mean in-OR time breakdown ──")
    print(valid.select(
        pl.col("patient_prep_min").mean().round(1).alias("patient_prep"),
        pl.col("procedure_min").mean().round(1).alias("procedure"),
        pl.col("post_procedure_min").mean().round(1).alias("post_procedure"),
        pl.col("actual_inor_min").mean().round(1).alias("total_actual"),
        pl.col("planned_inor_min").mean().round(1).alias("total_planned"),
    ))

    # ── 2. Share of in-OR time each phase consumes ───────────────────────────
    logger.info("\n── Each phase as % of actual in-OR time ──")
    shares = valid.filter(pl.col("actual_inor_min") > 0).with_columns([
        (pl.col("patient_prep_min") / pl.col("actual_inor_min") * 100).alias("prep_pct"),
        (pl.col("procedure_min") / pl.col("actual_inor_min") * 100).alias("procedure_pct"),
        (pl.col("post_procedure_min") / pl.col("actual_inor_min") * 100).alias("post_pct"),
    ])
    print(shares.select(
        pl.col("prep_pct").mean().round(1).alias("prep_%"),
        pl.col("procedure_pct").mean().round(1).alias("procedure_%"),
        pl.col("post_pct").mean().round(1).alias("post_procedure_%"),
    ))

    # ── 3. Planned slot vs actual total — how often does it run over? ────────
    logger.info("\n── Planned slot vs actual total ──")
    over = valid.with_columns(
        (pl.col("actual_inor_min") - pl.col("planned_inor_min")).alias("inor_gap_min")
    )
    pct_over = (over["inor_gap_min"] > 0).mean() * 100
    logger.info(f"Cases running over planned slot: {pct_over:.1f}%")
    logger.info(f"Mean gap (actual − planned):     {over['inor_gap_min'].mean():+.1f} min")

    # ── 4. Complexity: how prep share scales with staff/equipment ────────────
    logger.info(f"\n── Complexity vs phase durations (procedure level, n >= {MIN_CASES_PER_PROCEDURE}) ──")

    proc = (
        valid.filter(pl.col("procedure_text_id").is_not_null())
        .group_by("procedure_text_id")
        .agg(
            pl.len().alias("n"),
            pl.col("patient_prep_min").mean().alias("mean_prep"),
            pl.col("procedure_min").mean().alias("mean_procedure"),
            pl.col("post_procedure_min").mean().alias("mean_post"),
            pl.col("planned_inor_min").mean().alias("mean_planned"),
            pl.col("staff_count").mean().alias("mean_staff"),
            pl.col("resource_count").mean().alias("mean_resources"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_PROCEDURE)
    )
    logger.info(f"Procedures with n >= {MIN_CASES_PER_PROCEDURE}: {proc.shape[0]}")

    for phase, col in [("patient_prep", "mean_prep"), ("procedure", "mean_procedure"), ("post_procedure", "mean_post"), ("planned_inor", "mean_planned")]:
        r_staff = proc.select(pl.corr("mean_staff", col)).item()
        r_res   = proc.select(pl.corr("mean_resources", col)).item()
        logger.info(f"  {phase:20s}  staff r={r_staff:+.2f}  resources r={r_res:+.2f}")

    # ── 5. Breakdown by specialty ────────────────────────────────────────────
    logger.info("\n── In-OR breakdown by specialty (min 100 cases) ──")
    by_specialty = (
        valid.group_by("specialty")
        .agg(
            pl.col("patient_prep_min").mean().round(1).alias("prep"),
            pl.col("procedure_min").mean().round(1).alias("procedure"),
            pl.col("post_procedure_min").mean().round(1).alias("post"),
            pl.col("actual_inor_min").mean().round(1).alias("actual_total"),
            pl.col("planned_inor_min").mean().round(1).alias("planned_total"),
            pl.len().alias("n_cases"),
        )
        .with_columns(
            (pl.col("actual_total") - pl.col("planned_total")).round(1).alias("gap")
        )
        .filter(pl.col("n_cases") >= 100)
        .sort("prep", descending=True)
    )
    print(by_specialty)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
