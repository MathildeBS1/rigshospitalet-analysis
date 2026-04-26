"""
Plots for EDA 7: In-OR Time Decomposition

Figures:
  1. inor_breakdown_overall.png    — stacked bar: mean prep / procedure / post vs planned
  2. inor_breakdown_specialty.png  — stacked bar per specialty, sorted by prep time
  3. prep_vs_complexity.png        — scatter: staff count vs mean prep time (procedure level)
  4. planned_vs_actual_gap.png     — scatter: planned in-OR vs actual in-OR by specialty
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import polars as pl
import seaborn as sns
import numpy as np

from data.loader import load_completed
from utils.logger import get_logger

logger = get_logger(__name__)

FIGURES_DIR = Path(__file__).parent.parent.parent / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)
palette = sns.color_palette("muted")

C_PREP      = palette[3]   # muted red/salmon
C_PROCEDURE = palette[0]   # muted blue
C_POST      = palette[2]   # muted green
C_PLANNED   = palette[7]   # muted grey
C_SCATTER   = palette[0]


MIN_CASES_PER_PROCEDURE = 50
MIN_CASES_PER_SPECIALTY = 100


def _load(specialty=None):
    df = load_completed()
    if specialty:
        df = df.filter(pl.col("specialty") == specialty)

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

    return cases.filter(
        pl.col("patient_prep_min").is_between(0, 240),
        pl.col("procedure_min").is_between(0, 600),
        pl.col("post_procedure_min").is_between(0, 240),
        pl.col("planned_inor_min").is_between(0, 600),
    )


def plot_overall_breakdown(valid: pl.DataFrame) -> None:
    means = valid.select(
        pl.col("patient_prep_min").mean().alias("prep"),
        pl.col("procedure_min").mean().alias("procedure"),
        pl.col("post_procedure_min").mean().alias("post"),
        pl.col("planned_inor_min").mean().alias("planned"),
    ).row(0, named=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    # Stacked actual bar
    ax.bar(["Actual"], means["prep"],      color=C_PREP,      label="Patient prep")
    ax.bar(["Actual"], means["procedure"], color=C_PROCEDURE,  label="Procedure",  bottom=means["prep"])
    ax.bar(["Actual"], means["post"],      color=C_POST,       label="Post-procedure",
           bottom=means["prep"] + means["procedure"])

    # Planned as a single bar
    ax.bar(["Planned"], means["planned"], color=C_PLANNED, label="Planned in-OR")

    # Annotate segments on actual bar
    ax.text(0, means["prep"] / 2, f'{means["prep"]:.0f} min', ha="center", va="center", color="white", fontweight="bold")
    ax.text(0, means["prep"] + means["procedure"] / 2, f'{means["procedure"]:.0f} min', ha="center", va="center", color="white", fontweight="bold")
    ax.text(0, means["prep"] + means["procedure"] + means["post"] / 2, f'{means["post"]:.0f} min', ha="center", va="center", color="white", fontweight="bold")
    ax.text(1, means["planned"] / 2, f'{means["planned"]:.0f} min', ha="center", va="center", color="white", fontweight="bold")

    ax.set_ylabel("Minutes")
    ax.set_title("Mean In-OR Time: Actual Breakdown vs Planned Slot")
    ax.legend(loc="upper right")
    fig.tight_layout()
    _save(fig, "inor_breakdown_overall.png")


def plot_specialty_breakdown(valid: pl.DataFrame) -> None:
    by_specialty = (
        valid.group_by("specialty")
        .agg(
            pl.col("patient_prep_min").mean().round(1).alias("prep"),
            pl.col("procedure_min").mean().round(1).alias("procedure"),
            pl.col("post_procedure_min").mean().round(1).alias("post"),
            pl.col("planned_inor_min").mean().round(1).alias("planned"),
            pl.len().alias("n"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_SPECIALTY)
        .sort("prep", descending=False)
        .to_pandas()
    )

    fig, ax = plt.subplots(figsize=(12, 9))

    ax.barh(by_specialty["specialty"], by_specialty["prep"],      color=C_PREP,      label="Patient prep")
    ax.barh(by_specialty["specialty"], by_specialty["procedure"], color=C_PROCEDURE,  label="Procedure",
            left=by_specialty["prep"])
    ax.barh(by_specialty["specialty"], by_specialty["post"],      color=C_POST,       label="Post-procedure",
            left=by_specialty["prep"] + by_specialty["procedure"])

    # Planned as a vertical line per row
    for i, row in by_specialty.iterrows():
        y = list(by_specialty["specialty"]).index(row["specialty"])
        ax.plot([row["planned"], row["planned"]], [y - 0.4, y + 0.4],
                color=C_PLANNED, linewidth=2.5, zorder=5)

    planned_line = mpatches.Patch(color=C_PLANNED, label="Planned in-OR (line)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles + [planned_line], loc="lower right")

    ax.set_xlabel("Minutes")
    ax.set_title("In-OR Time Breakdown by Specialty (sorted by prep time)")
    fig.tight_layout()
    _save(fig, "inor_breakdown_specialty.png")


def plot_prep_vs_complexity(valid: pl.DataFrame) -> None:
    proc = (
        valid.filter(pl.col("procedure_text_id").is_not_null())
        .group_by("procedure_text_id")
        .agg(
            pl.len().alias("n"),
            pl.col("patient_prep_min").mean().alias("mean_prep"),
            pl.col("staff_count").mean().alias("mean_staff"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_PROCEDURE)
        .to_pandas()
    )

    r = np.corrcoef(proc["mean_staff"], proc["mean_prep"])[0, 1]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(
        proc["mean_staff"], proc["mean_prep"],
        s=proc["n"] / proc["n"].max() * 300 + 20,
        color=C_SCATTER, alpha=0.6, edgecolors="white", linewidth=0.5,
    )

    # Regression line
    m, b = np.polyfit(proc["mean_staff"], proc["mean_prep"], 1)
    x_line = np.linspace(proc["mean_staff"].min(), proc["mean_staff"].max(), 100)
    ax.plot(x_line, m * x_line + b, color=C_PREP, linewidth=2, linestyle="--")

    ax.set_xlabel("Mean staff count per procedure type")
    ax.set_ylabel("Mean patient prep time (min)")
    ax.set_title(f"Staff Complexity vs Patient Prep Time  (r = {r:+.2f}, n ≥ {MIN_CASES_PER_PROCEDURE} per procedure)")
    ax.text(0.97, 0.05, "Bubble size = number of cases", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color="grey")
    fig.tight_layout()
    _save(fig, "prep_vs_complexity.png")


def plot_planned_vs_actual_gap(valid: pl.DataFrame) -> None:
    by_specialty = (
        valid.group_by("specialty")
        .agg(
            pl.col("planned_inor_min").mean().round(1).alias("planned"),
            pl.col("actual_inor_min").mean().round(1).alias("actual"),
            pl.len().alias("n"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_SPECIALTY)
        .to_pandas()
    )

    fig, ax = plt.subplots(figsize=(9, 7))

    max_val = max(by_specialty["planned"].max(), by_specialty["actual"].max()) * 1.05
    ax.plot([0, max_val], [0, max_val], color="grey", linewidth=1.2,
            linestyle="--", label="Actual = Planned", zorder=1)

    ax.scatter(
        by_specialty["planned"], by_specialty["actual"],
        s=by_specialty["n"] / by_specialty["n"].max() * 400 + 40,
        color=C_SCATTER, alpha=0.7, edgecolors="white", linewidth=0.5, zorder=2,
    )

    for _, row in by_specialty.iterrows():
        ax.annotate(
            row["specialty"],
            (row["planned"], row["actual"]),
            xytext=(6, 4), textcoords="offset points",
            fontsize=8, color="dimgrey",
        )

    ax.set_xlabel("Mean planned in-OR time (min)")
    ax.set_ylabel("Mean actual in-OR time (min)")
    ax.set_title("Planned vs Actual In-OR Time by Specialty\n(above diagonal = runs over plan)")
    ax.legend()
    ax.text(0.97, 0.05, "Bubble size = number of cases", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, color="grey")
    fig.tight_layout()
    _save(fig, "planned_vs_actual_gap.png")


def _save(fig, filename):
    path = FIGURES_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.success(f"Saved → {path}")


def run():
    logger.info("Loading data...")
    valid = _load()
    logger.info(f"Cases: {valid.shape[0]:,}")

    plot_overall_breakdown(valid)
    plot_specialty_breakdown(valid)
    plot_prep_vs_complexity(valid)
    plot_planned_vs_actual_gap(valid)


if __name__ == "__main__":
    run()
