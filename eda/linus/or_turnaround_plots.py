"""
Plots for EDA 3: OR Turnaround Time Analysis

Three figures:
  1. turnaround_distribution.png  — histogram of overall turnaround times
  2. wasted_idle_by_specialty.png — stacked bar: idle before prep / OR prep / idle after prep
  3. turnaround_by_specialty.png  — box plot per specialty
"""

from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns

from utils.logger import get_logger
from data.loader import load_completed

logger = get_logger(__name__)

FIGURES_DIR = Path(__file__).parent.parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)

# Colours
C_IDLE_BEFORE = "#d95f02"   # orange  — wasted idle before prep
C_OR_PREP     = "#1b9e77"   # teal    — necessary OR prep
C_IDLE_AFTER  = "#fc8d59"   # peach   — wasted idle after prep (waiting for patient)
C_BLUE        = "#4a7bb5"   # blue    — neutral/distribution


def _prepare_data(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Returns:
      ta   — one row per consecutive case pair with turnaround_min
      idle — subset of ta with the full wasted/necessary breakdown
    """
    cases = (
        df.unique(subset=["case_id"], keep="first")
        .filter(
            pl.col("ts_patient_leaves_or").is_not_null(),
            pl.col("ts_patient_in_or").is_not_null(),
        )
        .sort(["or_room", "date", "ts_patient_in_or"])
        .with_columns(
            pl.col("ts_patient_leaves_or").shift(1).over(["or_room", "date"]).alias("prev_leaves_or"),
            pl.col("ts_or_cleaned").shift(1).over(["or_room", "date"]).alias("prev_or_cleaned"),
        )
    )

    ta = (
        cases
        .filter(pl.col("prev_leaves_or").is_not_null())
        .with_columns(
            (pl.col("ts_patient_in_or") - pl.col("prev_leaves_or"))
            .dt.total_minutes()
            .alias("turnaround_min")
        )
        .filter(pl.col("turnaround_min").is_between(0, 180))
    )

    idle = (
        ta
        .with_columns([
            (pl.col("ts_or_prep_start") - pl.col("prev_or_cleaned")).dt.total_minutes().alias("gap_before_prep_min"),
            (pl.col("ts_or_prep_done") - pl.col("ts_or_prep_start")).dt.total_minutes().alias("or_prep_duration_min"),
            (pl.col("ts_patient_in_or") - pl.col("ts_or_prep_done")).dt.total_minutes().alias("gap_after_prep_min"),
        ])
        .filter(
            pl.col("prev_or_cleaned").is_not_null(),
            pl.col("ts_or_prep_start").is_not_null(),
            pl.col("ts_or_prep_done").is_not_null(),
            pl.col("gap_before_prep_min").is_between(-5, 120),
            pl.col("or_prep_duration_min").is_between(0, 120),
            pl.col("gap_after_prep_min").is_between(-5, 120),
        )
    )

    return ta, idle


def plot_turnaround_distribution(ta: pl.DataFrame) -> None:
    mean_val = ta["turnaround_min"].mean()
    median_val = ta["turnaround_min"].median()

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(
        ta["turnaround_min"].to_list(),
        bins=60,
        kde=True,
        ax=ax,
        color=C_BLUE,
        edgecolor="white",
        linewidth=0.3,
    )
    ax.axvline(mean_val,   color=C_IDLE_BEFORE, linestyle="--", linewidth=1.8, label=f"Mean: {mean_val:.0f} min")
    ax.axvline(median_val, color=C_OR_PREP,     linestyle="--", linewidth=1.8, label=f"Median: {median_val:.0f} min")
    ax.set_xlabel("Turnaround time (minutes)")
    ax.set_ylabel("Number of case pairs")
    ax.set_title("OR Turnaround Time Distribution")
    ax.legend()
    fig.tight_layout()
    _save(fig, "turnaround_distribution.png")


def plot_wasted_idle_by_specialty(idle: pl.DataFrame) -> None:
    agg = (
        idle
        .group_by("specialty")
        .agg(
            pl.col("gap_before_prep_min").mean().alias("gap_before_prep"),
            pl.col("or_prep_duration_min").mean().alias("or_prep"),
            pl.col("gap_after_prep_min").mean().alias("gap_after_prep"),
            pl.len().alias("n_pairs"),
        )
        .filter(pl.col("n_pairs") >= 30)
        .with_columns(
            (pl.col("gap_before_prep") + pl.col("gap_after_prep")).alias("total_wasted")
        )
        .sort("total_wasted", descending=False)   # ascending → worst at top of chart
        .to_pandas()
    )

    fig, ax = plt.subplots(figsize=(11, 8))

    ax.barh(agg["specialty"], agg["gap_before_prep"], color=C_IDLE_BEFORE, label="Idle before prep starts")
    ax.barh(agg["specialty"], agg["or_prep"],
            left=agg["gap_before_prep"],
            color=C_OR_PREP, label="OR prep (necessary)")
    ax.barh(agg["specialty"], agg["gap_after_prep"],
            left=agg["gap_before_prep"] + agg["or_prep"],
            color=C_IDLE_AFTER, label="Idle after prep (waiting for patient)")

    ax.set_xlabel("Minutes")
    ax.set_title("OR Turnaround: Wasted Idle Time vs. Necessary Prep by Specialty")
    ax.legend(loc="lower right")
    fig.tight_layout()
    _save(fig, "wasted_idle_by_specialty.png")


def plot_turnaround_boxplot(ta: pl.DataFrame) -> None:
    order = (
        ta
        .group_by("specialty")
        .agg(
            pl.col("turnaround_min").median().alias("median"),
            pl.len().alias("n"),
        )
        .filter(pl.col("n") >= 50)
        .sort("median", descending=True)
        ["specialty"]
        .to_list()
    )

    pdf = ta.filter(pl.col("specialty").is_in(order)).to_pandas()

    fig, ax = plt.subplots(figsize=(12, 8))
    sns.boxplot(
        data=pdf,
        x="turnaround_min",
        y="specialty",
        order=order,
        ax=ax,
        color=C_BLUE,
        flierprops=dict(marker="o", markersize=2, alpha=0.3),
        whis=(5, 95),
    )
    ax.set_xlabel("Turnaround time (minutes)")
    ax.set_ylabel("")
    ax.set_title("OR Turnaround Time by Specialty  (whiskers = 5th–95th percentile)")
    fig.tight_layout()
    _save(fig, "turnaround_by_specialty.png")


def _save(fig: plt.Figure, filename: str) -> None:
    path = FIGURES_DIR / filename
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.success(f"Saved → {path}")


def run() -> None:
    logger.info("Loading data...")
    df = load_completed()
    ta, idle = _prepare_data(df)
    logger.info(f"Turnaround pairs: {ta.shape[0]:,}  |  pairs with full breakdown: {idle.shape[0]:,}")

    plot_turnaround_distribution(ta)
    plot_wasted_idle_by_specialty(idle)
    plot_turnaround_boxplot(ta)


if __name__ == "__main__":
    run()
