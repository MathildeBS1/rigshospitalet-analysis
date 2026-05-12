"""Finish overrun chart: how late patients leave the OR — current vs. lookup table.

Top panel:  Current schedule (bucketed by planned prep allocation)
Bottom panel: With lookup table (all cases, single bar)
"""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from data.loader import load_completed

RED = "#c0392b"
TEAL = "#1a8a7d"
MUTED = "#555555"
DARK = "#333333"
OUT = "poster/problem_overrun.png"

df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_patient_in_or_planned") - pl.col("ts_or_prep_planned_start"))
     .dt.total_seconds() / 60).alias("planned_prep_min"),
    ((pl.col("ts_patient_leaves_or") - pl.col("ts_patient_leaves_or_planned"))
     .dt.total_seconds() / 60).alias("room_overrun"),
    ((pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
     .dt.total_seconds() / 60).alias("w2_min"),
    pl.col("ts_anesthesia_start").is_not_null().alias("has_anesthesia"),
])

# --- Lookup table (specialty × anesthesia) ---
w2_filt = df.filter(
    pl.col("w2_min").is_not_null()
    & pl.col("w2_min").is_between(0, 240)
    & pl.col("specialty").is_not_null()
)
lookup = w2_filt.group_by(["specialty", "has_anesthesia"]).agg(
    pl.col("w2_min").mean().alias("lookup_prep")
)

df = df.join(lookup, on=["specialty", "has_anesthesia"], how="left")

# Counterfactual: new overrun = room_overrun - (lookup_prep - planned_prep)
df = df.with_columns(
    (pl.col("room_overrun") - (pl.col("lookup_prep") - pl.col("planned_prep_min")))
    .alias("new_overrun")
)

# --- Current schedule data ---
both = df.filter(
    pl.col("planned_prep_min").is_not_null()
    & pl.col("room_overrun").is_not_null()
)
total = both.shape[0]

buckets = [
    ("0 min",     pl.col("planned_prep_min") == 0),
    ("1–10 min",  (pl.col("planned_prep_min") > 0) & (pl.col("planned_prep_min") <= 10)),
    ("11–20 min", (pl.col("planned_prep_min") > 10) & (pl.col("planned_prep_min") <= 20)),
    ("20+ min",   pl.col("planned_prep_min") > 20),
]

labels, means, counts = [], [], []
for label, filt in buckets:
    s = both.filter(filt)
    labels.append(label)
    means.append(s["room_overrun"].mean())
    counts.append(s.shape[0])

# --- Lookup table data ---
both_fix = df.filter(
    pl.col("new_overrun").is_not_null()
    & pl.col("planned_prep_min").is_not_null()
    & pl.col("room_overrun").is_not_null()
)
fix_total = both_fix.shape[0]

fix_labels, fix_means, fix_counts = [], [], []
for label, filt in buckets:
    s = both_fix.filter(filt)
    fix_labels.append(label)
    fix_means.append(s["new_overrun"].mean())
    fix_counts.append(s.shape[0])

# --- Plot: two panels ---
fig = plt.figure(figsize=(16, 7.5))
gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1], hspace=0.35)

x_min, x_max = -20, 42

for panel_idx, (ax_gs, title, p_means, p_counts, p_total) in enumerate([
    (gs[0], "Current schedule", means, counts, total),
    (gs[1], "With lookup table", fix_means, fix_counts, fix_total),
]):
    ax = fig.add_subplot(ax_gs)
    is_fix = panel_idx == 1
    accent = TEAL if is_fix else RED

    y_pos = np.arange(len(labels))
    bar_height = 0.52
    colors = [RED if m > 0 else TEAL for m in p_means]

    ax.barh(y_pos, p_means, color=colors, height=bar_height, edgecolor="none", zorder=2)
    ax.axvline(x=0, color="#444444", linewidth=1.0, zorder=3)

    for i, (mean, count) in enumerate(zip(p_means, p_counts)):
        if mean > 0:
            x_text = mean + 0.8
            ha = "left"
        elif abs(mean) > 8:
            x_text = mean / 2
            ha = "center"
            colors[i] = "white"
        else:
            x_text = mean - 0.8
            ha = "right"
        ax.text(x_text, i, f"{mean:+.1f} min", va="center", ha=ha,
                fontsize=13, fontweight="bold", color=colors[i])

        pct = count / p_total * 100
        n_str = (f"n = {count:,}  ({pct:.0f}%)" if pct > 5
                 else f"n = {count:,}  ({pct:.1f}%)")
        ax.text(x_max - 1, i, n_str, va="center", ha="left", fontsize=10, color="#888888")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=14, fontweight="600")
    ax.invert_yaxis()
    ax.set_xlim(x_min, x_max)

    ax.set_title(title, fontsize=14, fontweight="bold", loc="left", pad=10, color=accent)
    ax.set_xlabel("Mean room departure overrun (minutes)", fontsize=11, color=MUTED)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, axis="y")
    ax.tick_params(axis="x", colors="#888888")
    ax.spines["bottom"].set_color("#cccccc")
    ax.xaxis.grid(True, color="#e8e8e8", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)

plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
print("\nCurrent schedule:")
for label, mean, count in zip(labels, means, counts):
    print(f"  {label}: mean={mean:+.1f}, n={count:,}")
print("\nWith lookup table:")
for label, mean, count in zip(fix_labels, fix_means, fix_counts):
    print(f"  {label}: mean={mean:+.1f}, n={count:,}")
