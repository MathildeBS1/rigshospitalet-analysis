"""
EDA 4: Planning Gap Analysis

Investigates whether the OR schedule accounts for cleaning and turnaround time
between consecutive cases, or whether cases are planned back-to-back with no buffer.

Key questions:
  1. How often is zero cleaning time planned (ts_or_cleaned_planned == ts_patient_leaves_or_planned)?
  2. How long does cleaning actually take when recorded?
  3. How large is the planned buffer between consecutive cases?
  4. Does a tighter planned buffer correlate with the next case starting late?
  5. What fraction of consecutive case pairs exceed their planned buffer?
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

    df = df.unique(subset=["case_id"], keep="first")
    n_total = df.shape[0]
    logger.info(f"Unique cases: {n_total:,}")

    # ── 1. Planned cleaning duration ─────────────────────────────────────────
    logger.info("\n── Planned cleaning duration (ts_or_cleaned_planned − ts_patient_leaves_or_planned) ──")

    planned_cleaning = df.filter(
        pl.col("ts_or_cleaned_planned").is_not_null(),
        pl.col("ts_patient_leaves_or_planned").is_not_null(),
    ).with_columns(
        (pl.col("ts_or_cleaned_planned") - pl.col("ts_patient_leaves_or_planned"))
        .dt.total_minutes()
        .alias("planned_cleaning_min")
    )

    n_with_planned = planned_cleaning.shape[0]
    n_zero = planned_cleaning.filter(pl.col("planned_cleaning_min") == 0).shape[0]
    logger.info(f"Cases with planned cleaning timestamps:  {n_with_planned:,} ({n_with_planned / n_total:.1%})")
    logger.info(f"Of those, planned cleaning = 0 minutes: {n_zero:,} ({n_zero / n_with_planned:.1%})")

    stats = planned_cleaning.filter(pl.col("planned_cleaning_min") > 0).select(
        pl.col("planned_cleaning_min").mean().round(1).alias("mean (>0 only)"),
        pl.col("planned_cleaning_min").median().round(1).alias("median (>0 only)"),
        pl.col("planned_cleaning_min").quantile(0.75).round(1).alias("p75 (>0 only)"),
    )
    print(stats)

    # ── 2. Actual cleaning duration (where recorded) ──────────────────────────
    logger.info("\n── Actual cleaning duration (ts_or_cleaned − ts_or_cleaning_start) ──")

    n_cleaning_recorded = df.filter(
        pl.col("ts_or_cleaning_start").is_not_null(),
        pl.col("ts_or_cleaned").is_not_null(),
    ).shape[0]
    logger.info(f"Cases with both cleaning timestamps recorded: {n_cleaning_recorded:,} ({n_cleaning_recorded / n_total:.1%})")

    actual_cleaning = df.filter(
        pl.col("ts_or_cleaning_start").is_not_null(),
        pl.col("ts_or_cleaned").is_not_null(),
    ).with_columns(
        (pl.col("ts_or_cleaned") - pl.col("ts_or_cleaning_start"))
        .dt.total_minutes()
        .alias("actual_cleaning_min")
    )

    n_zero_actual = actual_cleaning.filter(pl.col("actual_cleaning_min") == 0).shape[0]
    logger.info(
        f"Of those, actual cleaning = 0 minutes (same-timestamp entry): "
        f"{n_zero_actual:,} ({n_zero_actual / n_cleaning_recorded:.1%}) — likely data quality"
    )

    positive_cleaning = actual_cleaning.filter(
        pl.col("actual_cleaning_min").is_between(1, 120)
    )
    logger.info(f"Cases with meaningful cleaning duration (1–120 min): {positive_cleaning.shape[0]:,}")
    print(positive_cleaning.select(
        pl.col("actual_cleaning_min").mean().round(1).alias("mean_actual_cleaning_min"),
        pl.col("actual_cleaning_min").median().round(1).alias("median_actual_cleaning_min"),
        pl.col("actual_cleaning_min").quantile(0.25).round(1).alias("p25"),
        pl.col("actual_cleaning_min").quantile(0.75).round(1).alias("p75"),
        pl.col("actual_cleaning_min").quantile(0.90).round(1).alias("p90"),
    ))

    # ── 3. Planned buffer between consecutive cases ──────────────────────────
    logger.info("\n── Planned buffer between consecutive cases (planned_out[i] → planned_in[i+1]) ──")

    consecutive = (
        df.filter(
            pl.col("ts_patient_in_or_planned").is_not_null(),
            pl.col("ts_patient_leaves_or_planned").is_not_null(),
            pl.col("ts_patient_in_or").is_not_null(),
            pl.col("ts_patient_leaves_or").is_not_null(),
        )
        .sort(["or_room", "date", "ts_patient_in_or_planned"])
        .with_columns(
            pl.col("ts_patient_leaves_or_planned").shift(1).over(["or_room", "date"]).alias("prev_leaves_planned"),
            pl.col("ts_patient_leaves_or").shift(1).over(["or_room", "date"]).alias("prev_leaves_actual"),
        )
        .filter(pl.col("prev_leaves_planned").is_not_null())
        .with_columns(
            (pl.col("ts_patient_in_or_planned") - pl.col("prev_leaves_planned"))
            .dt.total_minutes()
            .alias("planned_buffer_min"),
            (pl.col("ts_patient_in_or") - pl.col("prev_leaves_actual"))
            .dt.total_minutes()
            .alias("actual_turnaround_min"),
            (pl.col("ts_patient_in_or") - pl.col("ts_patient_in_or_planned"))
            .dt.total_minutes()
            .alias("entry_delay_min"),
        )
        .filter(
            pl.col("planned_buffer_min").is_between(0, 120),
            pl.col("actual_turnaround_min").is_between(0, 180),
        )
    )

    n_pairs = consecutive.shape[0]
    n_zero_buffer = consecutive.filter(pl.col("planned_buffer_min") == 0).shape[0]
    logger.info(f"Consecutive case pairs analysed: {n_pairs:,}")
    logger.info(f"Pairs with 0 planned buffer: {n_zero_buffer:,} ({n_zero_buffer / n_pairs:.1%})")

    print(consecutive.select(
        pl.col("planned_buffer_min").mean().round(1).alias("mean_planned_buffer"),
        pl.col("planned_buffer_min").median().round(1).alias("median_planned_buffer"),
        pl.col("actual_turnaround_min").mean().round(1).alias("mean_actual_turnaround"),
        pl.col("actual_turnaround_min").median().round(1).alias("median_actual_turnaround"),
    ))

    # ── 4. Planned buffer vs. next case entry delay ───────────────────────────
    logger.info("\n── Next case entry delay by planned buffer size ──")

    by_buffer = (
        consecutive
        .with_columns(
            pl.when(pl.col("planned_buffer_min") == 0).then(pl.lit("0"))
            .when(pl.col("planned_buffer_min") <= 10).then(pl.lit("1–10"))
            .when(pl.col("planned_buffer_min") <= 20).then(pl.lit("11–20"))
            .when(pl.col("planned_buffer_min") <= 30).then(pl.lit("21–30"))
            .when(pl.col("planned_buffer_min") <= 45).then(pl.lit("31–45"))
            .otherwise(pl.lit("45+"))
            .alias("buffer_bucket")
        )
        .group_by("buffer_bucket")
        .agg(
            pl.col("entry_delay_min").mean().round(1).alias("mean_entry_delay_min"),
            pl.col("entry_delay_min").median().round(1).alias("median_entry_delay_min"),
            (pl.col("entry_delay_min") > 0).mean().mul(100).round(1).alias("pct_next_case_late"),
            pl.col("actual_turnaround_min").mean().round(1).alias("mean_actual_turnaround_min"),
            pl.len().alias("n_pairs"),
        )
        .sort("buffer_bucket")
    )
    print(by_buffer)

    corr = consecutive.select(pl.corr("planned_buffer_min", "entry_delay_min")).item()
    logger.info(f"Pearson r (planned buffer → next case entry delay): {corr:.3f}")

    # ── 5. How often does actual turnaround exceed the planned buffer? ────────
    logger.info("\n── Actual turnaround vs. planned buffer ──")

    exceeded = consecutive.with_columns(
        (pl.col("actual_turnaround_min") > pl.col("planned_buffer_min")).alias("exceeded"),
        (pl.col("actual_turnaround_min") - pl.col("planned_buffer_min")).alias("overshoot_min"),
    )

    pct_exceeded = exceeded["exceeded"].mean()
    mean_overshoot = exceeded.filter(pl.col("exceeded"))["overshoot_min"].mean()
    logger.info(f"Pairs where actual turnaround exceeded planned buffer: {pct_exceeded:.1%}")
    logger.info(f"Mean overshoot when exceeded: {mean_overshoot:.1f} min")

    # Overshoot by buffer size
    logger.info("\n── Overshoot by planned buffer size ──")
    overshoot_by_bucket = (
        exceeded
        .with_columns(
            pl.when(pl.col("planned_buffer_min") == 0).then(pl.lit("0"))
            .when(pl.col("planned_buffer_min") <= 10).then(pl.lit("1–10"))
            .when(pl.col("planned_buffer_min") <= 20).then(pl.lit("11–20"))
            .when(pl.col("planned_buffer_min") <= 30).then(pl.lit("21–30"))
            .when(pl.col("planned_buffer_min") <= 45).then(pl.lit("31–45"))
            .otherwise(pl.lit("45+"))
            .alias("buffer_bucket")
        )
        .group_by("buffer_bucket")
        .agg(
            pl.col("exceeded").mean().mul(100).round(1).alias("pct_exceeded"),
            pl.col("overshoot_min").filter(pl.col("exceeded")).mean().round(1).alias("mean_overshoot_when_exceeded_min"),
            pl.len().alias("n_pairs"),
        )
        .sort("buffer_bucket")
    )
    print(overshoot_by_bucket)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
