"""
EDA 1: Delay Cascade Analysis

Investigates whether a late start early in the day compounds into larger delays
for operations later in the same OR.
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

    # One row per case — multiple rows exist per case due to multiple procedures
    cases = df.unique(subset=["case_id"], keep="first")
    logger.info(f"Unique cases: {cases.shape[0]:,}")

    # Keep only cases with planned + actual OR entry and a delay value
    cases = cases.filter(
        pl.col("ts_patient_in_or_planned").is_not_null(),
        pl.col("ts_patient_in_or").is_not_null(),
        pl.col("delay_minutes").is_not_null(),
    )
    logger.info(f"Cases with full timing data: {cases.shape[0]:,}")

    # Assign each case a position within its OR room's daily schedule (1 = first of the day)
    cases = cases.with_columns(
        pl.col("ts_patient_in_or_planned")
        .rank("ordinal")
        .over(["or_room", "date"])
        .cast(pl.Int32)
        .alias("case_position"),
    ).with_columns(
        pl.col("case_position")
        .max()
        .over(["or_room", "date"])
        .alias("cases_in_day"),
    )

    # ── 1. Mean delay by position in OR day ─────────────────────────────────
    logger.info("\n── Mean delay by case position in OR day ──")
    by_position = (
        cases
        .with_columns(
            pl.when(pl.col("case_position") >= 5)
            .then(pl.lit("5+"))
            .otherwise(pl.col("case_position").cast(pl.String))
            .alias("position_label")
        )
        .group_by("position_label")
        .agg(
            pl.col("delay_minutes").mean().round(1).alias("mean_delay_min"),
            pl.col("delay_minutes").median().round(1).alias("median_delay_min"),
            (pl.col("delay_minutes") > 0).mean().mul(100).round(1).alias("pct_delayed"),
            pl.len().alias("n_cases"),
        )
        .sort("position_label")
    )
    print(by_position)

    # ── 2. Pearson correlation: first-case delay → mean delay of later cases ─
    logger.info("\n── Cascade correlation: first-case delay vs. mean delay of later cases ──")

    first_cases = (
        cases
        .filter(pl.col("case_position") == 1)
        .select(["or_room", "date", pl.col("delay_minutes").alias("first_delay")])
    )

    later_cases = (
        cases
        .filter(pl.col("case_position") > 1)
        .group_by(["or_room", "date"])
        .agg(
            pl.col("delay_minutes").mean().alias("mean_later_delay"),
            pl.len().alias("n_later_cases"),
        )
        .filter(pl.col("n_later_cases") >= 2)
    )

    paired = first_cases.join(later_cases, on=["or_room", "date"], how="inner")

    corr = paired.select(pl.corr("first_delay", "mean_later_delay")).item()
    n_or_days = paired.shape[0]
    pct_cascade = (
        paired.filter(pl.col("mean_later_delay") > pl.col("first_delay")).shape[0]
        / n_or_days
    )

    logger.info(f"OR days analysed (≥2 later cases): {n_or_days:,}")
    logger.info(f"Pearson r (first delay → mean later delay): {corr:.3f}")
    logger.info(f"OR days where later cases are more delayed than first: {pct_cascade:.1%}")

    # ── 3. Top 10 worst cascade days ────────────────────────────────────────
    logger.info("\n── Top 10 worst cascade days (last case delay − first case delay) ──")

    last_cases = (
        cases
        .with_columns(
            pl.col("case_position").max().over(["or_room", "date"]).alias("max_position")
        )
        .filter(
            pl.col("case_position") == pl.col("max_position"),
            pl.col("max_position") >= 3,
        )
        .select(["or_room", "date", pl.col("delay_minutes").alias("last_delay"), "max_position"])
        .rename({"max_position": "n_cases"})
    )

    worst = (
        first_cases
        .join(last_cases, on=["or_room", "date"], how="inner")
        .with_columns(
            (pl.col("last_delay") - pl.col("first_delay")).alias("cascade_gap_min")
        )
        .sort("cascade_gap_min", descending=True)
        .head(10)
        .select(["date", "or_room", "n_cases", "first_delay", "last_delay", "cascade_gap_min"])
    )
    print(worst)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
