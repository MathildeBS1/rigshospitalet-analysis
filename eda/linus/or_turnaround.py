"""
EDA 3: OR Turnaround Time Analysis

Measures the idle time between consecutive cases in the same OR room and breaks
it down into: wait before cleaning starts, cleaning duration, and idle time after
cleaning until the next patient arrives.

Also shows planned vs. actual duration by specialty to surface chronic over/under-estimation.
"""

import polars as pl

from utils.logger import get_logger
from data.loader import load_completed

logger = get_logger(__name__)


def run(specialty: str | None = None) -> None:
    logger.info("Loading completed operations...")
    df = load_completed()

    if specialty:
        df = df.filter(pl.col("specialty") == specialty)
        logger.info(f"Filtered to specialty: {specialty}")

    cases = df.unique(subset=["case_id"], keep="first").filter(
        pl.col("ts_patient_leaves_or").is_not_null(),
        pl.col("ts_patient_in_or").is_not_null(),
    )
    logger.info(f"Cases with OR entry/exit timestamps: {cases.shape[0]:,}")

    # Sort so shift(1) gives the previous case in the same OR on the same day
    cases = cases.sort(["or_room", "date", "ts_patient_in_or"])

    # Shift all timestamps from the previous case that we need for the breakdown
    cases = cases.with_columns(
        pl.col("ts_patient_leaves_or").shift(1).over(["or_room", "date"]).alias("prev_leaves_or"),
        pl.col("ts_or_cleaning_start").shift(1).over(["or_room", "date"]).alias("prev_or_cleaning_start"),
        pl.col("ts_or_cleaned").shift(1).over(["or_room", "date"]).alias("prev_or_cleaned"),
    )

    # Keep only rows that have a preceding case in the same OR on the same day
    ta = cases.filter(pl.col("prev_leaves_or").is_not_null()).with_columns(
        (pl.col("ts_patient_in_or") - pl.col("prev_leaves_or"))
        .dt.total_minutes()
        .alias("turnaround_min")
    )

    # Negative turnaround = data entry error; >180 min = likely a session gap, not a turnaround
    ta = ta.filter(pl.col("turnaround_min").is_between(0, 180))
    logger.info(f"Consecutive case pairs (turnaround 0–180 min): {ta.shape[0]:,}")

    # Breakdown components — all relative to the PREVIOUS case's cleaning timestamps
    ta = ta.with_columns([
        pl.when(pl.col("prev_or_cleaning_start").is_not_null())
        .then((pl.col("prev_or_cleaning_start") - pl.col("prev_leaves_or")).dt.total_minutes())
        .alias("wait_before_cleaning_min"),

        pl.when(
            pl.col("prev_or_cleaning_start").is_not_null()
            & pl.col("prev_or_cleaned").is_not_null()
        )
        .then((pl.col("prev_or_cleaned") - pl.col("prev_or_cleaning_start")).dt.total_minutes())
        .alias("cleaning_duration_min"),

        # Includes OR prep for the next case (ts_or_prep_start → ts_or_prep_done) — not purely idle
        pl.when(pl.col("prev_or_cleaned").is_not_null())
        .then((pl.col("ts_patient_in_or") - pl.col("prev_or_cleaned")).dt.total_minutes())
        .alias("post_cleaning_gap_min"),
    ])

    # ── 1. Overall turnaround distribution ──────────────────────────────────
    logger.info("\n── Overall turnaround time distribution (minutes) ──")
    overall = ta.select(
        pl.col("turnaround_min").mean().round(1).alias("mean"),
        pl.col("turnaround_min").median().round(1).alias("median"),
        pl.col("turnaround_min").quantile(0.25).round(1).alias("p25"),
        pl.col("turnaround_min").quantile(0.75).round(1).alias("p75"),
        pl.col("turnaround_min").quantile(0.90).round(1).alias("p90"),
    )
    print(overall)

    # ── 2. Turnaround breakdown (where timestamps available) ─────────────────
    logger.info("\n── Mean turnaround components (minutes) ──")
    breakdown = ta.select(
        pl.col("wait_before_cleaning_min").mean().round(1).alias("wait_before_cleaning"),
        pl.col("cleaning_duration_min").mean().round(1).alias("cleaning_duration"),
        pl.col("post_cleaning_gap_min").mean().round(1).alias("post_cleaning_gap"),
        pl.col("wait_before_cleaning_min").is_not_null().mean().mul(100).round(1).alias("cleaning_timestamp_coverage_pct"),
    )
    print(breakdown)

    # ── 3. Turnaround by specialty ───────────────────────────────────────────
    logger.info("\n── Mean turnaround by specialty (min 50 pairs) ──")
    by_specialty = (
        ta
        .group_by("specialty")
        .agg(
            pl.col("turnaround_min").mean().round(1).alias("mean_turnaround_min"),
            pl.col("turnaround_min").median().round(1).alias("median_turnaround_min"),
            pl.col("post_cleaning_gap_min").mean().round(1).alias("mean_post_cleaning_gap_min"),
            pl.len().alias("n_pairs"),
        )
        .filter(pl.col("n_pairs") >= 50)
        .sort("mean_turnaround_min", descending=True)
    )
    print(by_specialty)

    # ── 4. Wasted idle time vs. necessary OR prep ───────────────────────────
    # post_cleaning_gap = gap_before_prep + or_prep_duration + gap_after_prep
    #   gap_before_prep:   OR is clean but prep hasn't started yet   → wasted
    #   or_prep_duration:  setting up equipment for next case         → necessary
    #   gap_after_prep:    OR is ready but patient hasn't arrived yet → wasted
    logger.info("\n── Wasted idle time vs. necessary OR prep ──")

    idle = ta.with_columns([
        (pl.col("ts_or_prep_start") - pl.col("prev_or_cleaned")).dt.total_minutes().alias("gap_before_prep_min"),
        (pl.col("ts_or_prep_done") - pl.col("ts_or_prep_start")).dt.total_minutes().alias("or_prep_duration_min"),
        (pl.col("ts_patient_in_or") - pl.col("ts_or_prep_done")).dt.total_minutes().alias("gap_after_prep_min"),
    ]).filter(
        pl.col("prev_or_cleaned").is_not_null(),
        pl.col("ts_or_prep_start").is_not_null(),
        pl.col("ts_or_prep_done").is_not_null(),
        # Clamp out obvious data entry errors
        pl.col("gap_before_prep_min").is_between(-5, 120),
        pl.col("or_prep_duration_min").is_between(0, 120),
        pl.col("gap_after_prep_min").is_between(-5, 120),
    )

    n_idle = idle.shape[0]
    logger.info(f"Pairs with full breakdown timestamps: {n_idle:,} ({n_idle / ta.shape[0]:.1%} of turnaround pairs)")

    overall_idle = idle.select(
        pl.col("gap_before_prep_min").mean().round(1).alias("mean_gap_before_prep"),
        pl.col("or_prep_duration_min").mean().round(1).alias("mean_or_prep_duration"),
        pl.col("gap_after_prep_min").mean().round(1).alias("mean_gap_after_prep"),
        (pl.col("gap_before_prep_min") + pl.col("gap_after_prep_min")).mean().round(1).alias("mean_total_wasted"),
        pl.col("turnaround_min").mean().round(1).alias("mean_turnaround"),
    )
    print(overall_idle)

    logger.info("\n── Wasted idle time breakdown by specialty (min 30 pairs) ──")
    idle_by_specialty = (
        idle
        .with_columns(
            (pl.col("gap_before_prep_min") + pl.col("gap_after_prep_min")).alias("total_wasted_min")
        )
        .group_by("specialty")
        .agg(
            pl.col("total_wasted_min").mean().round(1).alias("mean_wasted_min"),
            pl.col("gap_before_prep_min").mean().round(1).alias("mean_gap_before_prep_min"),
            pl.col("or_prep_duration_min").mean().round(1).alias("mean_or_prep_min"),
            pl.col("gap_after_prep_min").mean().round(1).alias("mean_gap_after_prep_min"),
            pl.col("turnaround_min").mean().round(1).alias("mean_turnaround_min"),
            pl.len().alias("n_pairs"),
        )
        .filter(pl.col("n_pairs") >= 30)
        .sort("mean_wasted_min", descending=True)
    )
    print(idle_by_specialty)

    # ── 5. Planned vs. actual duration by specialty ──────────────────────────
    # Uses overtime_minutes: negative = finished early, positive = ran over
    logger.info("\n── Planned vs. actual duration by specialty (overtime_minutes) ──")
    duration_cases = df.unique(subset=["case_id"], keep="first").filter(
        pl.col("overtime_minutes").is_not_null(),
        pl.col("ts_procedure_start").is_not_null(),
        pl.col("ts_procedure_end").is_not_null(),
    )

    by_specialty_duration = (
        duration_cases
        .group_by("specialty")
        .agg(
            pl.col("overtime_minutes").mean().round(1).alias("mean_overtime_min"),
            pl.col("overtime_minutes").median().round(1).alias("median_overtime_min"),
            (pl.col("overtime_minutes") > 0).mean().mul(100).round(1).alias("pct_over_planned"),
            (pl.col("overtime_minutes") < 0).mean().mul(100).round(1).alias("pct_under_planned"),
            pl.len().alias("n_cases"),
        )
        .filter(pl.col("n_cases") >= 50)
        .sort("mean_overtime_min")
    )
    print(by_specialty_duration)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
