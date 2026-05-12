"""Panel 3: Before/after Gantt — same OR day, current vs lookup schedule."""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.path import Path
from matplotlib.transforms import blended_transform_factory
from datetime import datetime
from data.loader import load_completed

RED = "#c0392b"
TEAL = "#1a8a7d"
PREP_COLOR = "#1a6b5a"
PREP_LIGHT = "#c2e0d8"
SURGERY_COLOR = "#2c6faa"
SURGERY_LIGHT = "#b8d4ec"
GRAY_TEXT = "#555555"
GRAY_LIGHT = "#e8e8e8"
BRACE_COLOR = "#999999"

OUT = "poster/fix_gantt.png"

# --- Load and compute columns ---
df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_patient_in_or_planned") - pl.col("ts_or_prep_planned_start"))
     .dt.total_seconds() / 60).alias("planned_prep_min"),
    ((pl.col("ts_patient_in_or") - pl.col("ts_patient_in_or_planned"))
     .dt.total_seconds() / 60).alias("start_delay_min"),
    ((pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
     .dt.total_seconds() / 60).alias("w2_min"),
    ((pl.col("ts_procedure_end") - pl.col("ts_procedure_start"))
     .dt.total_seconds() / 60).alias("surgery_dur_min"),
    ((pl.col("ts_procedure_end") - pl.col("ts_patient_leaves_or_planned"))
     .dt.total_seconds() / 60).alias("overrun_min"),
    pl.col("ts_anesthesia_start").is_not_null().alias("has_anesthesia"),
])

# Compute lookup table (specialty × anesthesia)
w2_filt = df.filter(
    pl.col("w2_min").is_not_null()
    & pl.col("w2_min").is_between(0, 240)
    & pl.col("specialty").is_not_null()
)
lookup = w2_filt.group_by(["specialty", "has_anesthesia"]).agg(
    pl.col("w2_min").mean().alias("lookup_prep")
)

# --- Find OR day: overrun present, and fix prep fits in gap between cases ---
candidates = (
    df.filter(
        pl.col("planned_prep_min").is_not_null()
        & (pl.col("planned_prep_min") == 0)
        & pl.col("start_delay_min").is_not_null()
        & pl.col("w2_min").is_not_null()
        & pl.col("surgery_dur_min").is_not_null()
        & (pl.col("surgery_dur_min").is_between(20, 180))
        & pl.col("overrun_min").is_not_null()
        & (pl.col("overrun_min").is_between(10, 90))
        & pl.col("specialty").is_not_null()
        & pl.col("ts_procedure_end").is_not_null()
        & (pl.col("ts_patient_in_or_planned").dt.hour().is_between(7, 16))
    )
    .join(lookup, on=["specialty", "has_anesthesia"])
    .filter(pl.col("lookup_prep") > 20)
)

or_days = (
    candidates
    .group_by(["or_room", "date"])
    .agg([
        pl.len().alias("n_cases"),
        pl.col("start_delay_min").mean().alias("mean_start_delay"),
        pl.col("overrun_min").mean().alias("mean_overrun"),
    ])
    .filter(
        (pl.col("n_cases").is_between(3, 4))
        & (pl.col("mean_overrun") > 15)
        & (pl.col("mean_overrun") < 90)
    )
    .sort("mean_overrun", descending=True)
)

best_room, best_date = None, None
for day in or_days.iter_rows(named=True):
    day_cases = (
        candidates
        .filter(
            (pl.col("or_room") == day["or_room"])
            & (pl.col("date") == day["date"])
        )
        .sort("ts_patient_in_or_planned")
        .head(3)
    )
    day_rows = day_cases.to_dicts()

    # Constraint: allocated prep for case k+1 must not start before
    # the allocated end of case k (planned_end[k] + lookup_prep[k])
    feasible = True
    for k in range(len(day_rows) - 1):
        gap = (day_rows[k + 1]["ts_patient_in_or_planned"]
               - day_rows[k]["ts_patient_leaves_or_planned"]).total_seconds() / 60
        if gap < day_rows[k]["lookup_prep"]:
            feasible = False
            break

    if feasible:
        best_room, best_date = day["or_room"], day["date"]
        cases = day_cases
        break

if best_room is None:
    raise RuntimeError("No feasible OR day found")

rows = cases.to_dicts()
n_cases = len(rows)

t0_dt = datetime.combine(best_date, datetime.min.time().replace(hour=7))


def to_min(ts):
    return (ts - t0_dt).total_seconds() / 60


# Compute x-axis range from planned + actual extents
all_starts = []
all_ends = []
for c in rows:
    lkp = c["lookup_prep"]
    plan_s = to_min(c["ts_patient_in_or_planned"])
    all_starts.append(plan_s)
    all_starts.append(to_min(c["ts_patient_in_or"]))
    all_ends.append(to_min(c["ts_procedure_end"]))
    plan_end_s = to_min(c["ts_patient_leaves_or_planned"])
    all_ends.append(plan_end_s + lkp)

x_min = -5
x_max = max(all_ends) + 15


# --- Curly brace helper ---
def draw_brace(ax, y_top_data, y_bot_data, x_frac=0.058, w_frac=0.016,
               color=BRACE_COLOR, lw=1.3):
    """Draw a curly brace { in pure axes coords (converts y from data)."""
    y_lim = ax.get_ylim()
    y_top = (y_top_data - y_lim[0]) / (y_lim[1] - y_lim[0])
    y_bot = (y_bot_data - y_lim[0]) / (y_lim[1] - y_lim[0])
    height = y_top - y_bot
    curliness = 1 / np.e

    verts = np.array([
        [w_frac, 0],
        [0, 0],
        [w_frac, curliness],
        [0, 0.5],
        [w_frac, 1 - curliness],
        [0, 1],
        [w_frac, 1],
    ])
    verts[:, 1] = y_bot + verts[:, 1] * height
    verts[:, 0] = (x_frac - w_frac) + verts[:, 0]

    codes = [Path.MOVETO] + [Path.CURVE4] * 6
    path = Path(verts, codes)
    patch = mpatches.PathPatch(
        path, facecolor="none", edgecolor=color, lw=lw,
        capstyle="round", transform=ax.transAxes, clip_on=False, zorder=5)
    ax.add_patch(patch)


# --- Plot ---
CASE_SPACING = 1.6
fig, axes = plt.subplots(2, 1, figsize=(20, 7.5), sharex=True,
                         gridspec_kw={"hspace": 0.30})

bar_h = 0.38
gap = 0.12

for panel_idx, (ax, title) in enumerate(zip(axes, [
    "Current schedule  (0 min prep allocated)",
    "With lookup table  (prep allocated per specialty)",
])):
    is_fix = panel_idx == 1
    accent = TEAL if is_fix else RED

    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=10,
                 color=accent)

    # Set limits first so brace coordinate conversion works
    y_max_data = (n_cases - 1) * CASE_SPACING
    ax.set_ylim(-1.2, y_max_data + 1.0)
    ax.set_xlim(x_min, x_max)

    brace_info = []

    for i, c in enumerate(rows):
        y = (n_cases - 1 - i) * CASE_SPACING

        plan_start = to_min(c["ts_patient_in_or_planned"])
        plan_end = to_min(c["ts_patient_leaves_or_planned"])
        real_in = to_min(c["ts_patient_in_or"])
        proc_start = to_min(c["ts_procedure_start"])
        proc_end = to_min(c["ts_procedure_end"])
        lkp = c["lookup_prep"]

        y_plan = y + gap + bar_h / 2
        y_real = y - gap - bar_h / 2

        # --- Planned allocation bar ---
        if is_fix:
            ax.barh(y_plan, lkp, left=plan_start,
                    height=bar_h, color=PREP_LIGHT, edgecolor=PREP_COLOR,
                    linewidth=0.8, zorder=2)
            new_surg_start = plan_start + lkp
            ax.barh(y_plan, plan_end - plan_start, left=new_surg_start,
                    height=bar_h, color=SURGERY_LIGHT, edgecolor=SURGERY_COLOR,
                    linewidth=0.8, zorder=2)
        else:
            ax.barh(y_plan, plan_end - plan_start, left=plan_start,
                    height=bar_h, color=SURGERY_LIGHT, edgecolor=SURGERY_COLOR,
                    linewidth=0.8, zorder=2)

        # --- Actual bar: prep (always teal) + surgery (always blue) ---
        ax.barh(y_real, proc_start - real_in, left=real_in,
                height=bar_h, color=PREP_COLOR, edgecolor="none",
                alpha=0.85, zorder=2)
        ax.barh(y_real, proc_end - proc_start, left=proc_start,
                height=bar_h, color=SURGERY_COLOR, edgecolor="none",
                alpha=0.55, zorder=2)

        # Save brace positions for after limits are set
        brace_info.append((i, y, y_plan + bar_h / 2, y_real - bar_h / 2))

        # --- Overrun annotation: planned finish vs actual finish ---
        tick_h = 0.03
        if is_fix:
            ref_end = plan_end + lkp       # new planned end accounts for prep
            overrun = proc_end - ref_end
        else:
            ref_end = plan_end             # current planned end
            overrun = c["overrun_min"]

        left_pt = min(ref_end, proc_end)
        right_pt = max(ref_end, proc_end)
        mid = (left_pt + right_pt) / 2

        if abs(overrun) < 3:
            ax.text(mid, y + bar_h + gap + 0.20,
                    "on time", ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color=TEAL)
        else:
            sign = "+" if overrun > 0 else ""
            col = RED if overrun > 0 else TEAL
            ax.plot([left_pt, right_pt], [y, y],
                    color=col, lw=1.5, zorder=4)
            ax.plot([left_pt, left_pt], [y - tick_h, y + tick_h],
                    color=col, lw=1.5, zorder=4)
            ax.plot([right_pt, right_pt], [y - tick_h, y + tick_h],
                    color=col, lw=1.5, zorder=4)
            ax.text(mid, y + bar_h + gap + 0.20,
                    f"{sign}{overrun:.0f} min",
                    ha="center", va="bottom",
                    fontsize=10, fontweight="bold", color=col)

    # --- Draw curly braces + case labels (after ylim is set) ---
    for i, y, brace_top, brace_bot in brace_info:
        draw_brace(ax, brace_top, brace_bot)
        trans = blended_transform_factory(ax.transAxes, ax.transData)
        ax.text(0.022, y, f"Case {i + 1}", ha="right", va="center",
                fontsize=10, fontweight="600", color=GRAY_TEXT,
                transform=trans)

    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, axis="y")
    ax.tick_params(axis="x", colors="#888888")
    ax.spines["bottom"].set_color("#cccccc")
    ax.xaxis.grid(True, color=GRAY_LIGHT, linewidth=0.5)
    ax.set_axisbelow(True)

# Format x-axis as clock times
import matplotlib.ticker as mticker

def fmt_clock(x, pos):
    h = t0_dt.hour + int(x) // 60
    m = int(x) % 60
    return f"{h:02d}:{m:02d}"

axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(fmt_clock))
axes[1].set_xlabel("Time of day", fontsize=11, color=GRAY_TEXT)

# Legend
import matplotlib.lines as mlines
legend_elements = [
    mpatches.Patch(facecolor=PREP_LIGHT, edgecolor=PREP_COLOR, linewidth=0.8,
                   label="Planned prep"),
    mpatches.Patch(facecolor=PREP_COLOR, alpha=0.85,
                   label="Actual prep"),
    mpatches.Patch(facecolor=SURGERY_LIGHT, edgecolor=SURGERY_COLOR, linewidth=0.8,
                   label="Planned surgery"),
    mpatches.Patch(facecolor=SURGERY_COLOR, alpha=0.55,
                   label="Actual surgery"),
    mlines.Line2D([0, 1], [0, 0], color=GRAY_TEXT, linewidth=1.5,
                  marker="|", markersize=8, markeredgewidth=1.5,
                  label="Overrun"),
]
fig.legend(handles=legend_elements, loc="lower center", ncol=5, fontsize=10,
           frameon=False, bbox_to_anchor=(0.5, -0.01))

plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
print(f"OR day: {best_room}, {best_date}")
for i, c in enumerate(rows):
    lkp = c["lookup_prep"]
    overrun = c["overrun_min"]
    new_overrun = overrun - lkp
    print(f"  Case {i+1}: start_delay={c['start_delay_min']:.0f} min, "
          f"overrun {overrun:.0f} → {new_overrun:.0f} min "
          f"(lookup={lkp:.0f}, specialty={c['specialty']})")
