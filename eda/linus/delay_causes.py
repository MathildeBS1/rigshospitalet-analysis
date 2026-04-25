"""
EDA 2: Delay Causes Analysis

Identifies the top delay reasons overall and broken down by surgical specialty,
including total OR time lost per reason.
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

    # One row per case
    cases = df.unique(subset=["case_id"], keep="first")
    n_total = cases.shape[0]
    logger.info(f"Unique cases: {n_total:,}")

    # Cases with a positive delay and a recorded reason
    delayed = cases.filter(
        pl.col("delay_minutes") > 0,
        pl.col("delay_reason").is_not_null(),
    )
    n_delayed = delayed.shape[0]
    logger.info(f"Cases with delay + recorded reason: {n_delayed:,} ({n_delayed / n_total:.1%} of all cases)")

    # ── 1. Top delay reasons overall ────────────────────────────────────────
    logger.info("\n── Top 15 delay reasons overall ──")
    top_reasons = (
        delayed
        .group_by("delay_reason")
        .agg(
            pl.len().alias("n_cases"),
            pl.col("delay_minutes").mean().round(1).alias("mean_delay_min"),
            (pl.col("delay_minutes").sum() / 60).round(1).alias("total_hours_lost"),
        )
        .with_columns(
            (pl.col("n_cases") / n_delayed * 100).round(1).alias("pct_of_delayed")
        )
        .sort("n_cases", descending=True)
        .head(15)
        .select(["delay_reason", "n_cases", "pct_of_delayed", "mean_delay_min", "total_hours_lost"])
    )
    print(top_reasons)

    # ── 2. Top delay reason per specialty ───────────────────────────────────
    logger.info("\n── Top delay reason per specialty ──")
    top_per_specialty = (
        delayed
        .group_by(["specialty", "delay_reason"])
        .agg(
            pl.len().alias("count"),
            pl.col("delay_minutes").mean().round(1).alias("mean_delay_min"),
        )
        .with_columns(
            pl.col("count").rank("ordinal", descending=True).over("specialty").alias("rank")
        )
        .filter(pl.col("rank") == 1)
        .sort("count", descending=True)
        .select(["specialty", "delay_reason", "count", "mean_delay_min"])
    )
    print(top_per_specialty)

    # ── 3. Total OR time lost by reason (top 10) ────────────────────────────
    logger.info("\n── Total OR time lost per delay reason (top 10) ──")
    time_lost = (
        delayed
        .group_by("delay_reason")
        .agg(
            pl.len().alias("n_cases"),
            (pl.col("delay_minutes").sum() / 60).round(1).alias("total_hours_lost"),
            pl.col("delay_minutes").mean().round(1).alias("mean_delay_min"),
        )
        .sort("total_hours_lost", descending=True)
        .head(10)
        .select(["delay_reason", "n_cases", "total_hours_lost", "mean_delay_min"])
    )
    print(time_lost)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
