"""Problem panel: Anscombe-style reveal + diverging bar punchline."""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.stats import gaussian_kde
from data.loader import load_completed

RED = "#c0392b"
TEAL = "#1a8a7d"
DARK = "#333333"
MUTED = "#555555"

OUT = "poster/explore_anscombe.png"

df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_patient_in_or_planned") - pl.col("ts_or_prep_planned_start"))
     .dt.total_seconds() / 60).alias("planned_prep_min"),
    ((pl.col("ts_patient_in_or") - pl.col("ts_patient_in_or_planned"))
     .dt.total_seconds() / 60).alias("start_delay_min"),
])

# Unfiltered for bar chart stats (matches problem_chart.py)
both_full = df.filter(
    pl.col("planned_prep_min").is_not_null()
    & pl.col("start_delay_min").is_not_null()
)
total = both_full.shape[0]

# Range-filtered for density visualization
both = both_full.filter(pl.col("start_delay_min").is_between(-60, 120))

all_delays = both["start_delay_min"].to_numpy()
zero_prep = both.filter(pl.col("planned_prep_min") == 0)["start_delay_min"].to_numpy()
has_prep = both.filter(pl.col("planned_prep_min") > 0)["start_delay_min"].to_numpy()

frac_zero = len(zero_prep) / len(all_delays)
frac_has = len(has_prep) / len(all_delays)

x_grid = np.linspace(-60, 120, 500)
kde_all = gaussian_kde(all_delays, bw_method=0.15)
kde_zero = gaussian_kde(zero_prep, bw_method=0.15)
kde_has = gaussian_kde(has_prep, bw_method=0.15)

# --- Diverging bar data (from unfiltered, matching problem_chart.py) ---
buckets = [
    ("0 min",     pl.col("planned_prep_min") == 0),
    ("1–10",      (pl.col("planned_prep_min") > 0) & (pl.col("planned_prep_min") <= 10)),
    ("11–20",     (pl.col("planned_prep_min") > 10) & (pl.col("planned_prep_min") <= 20)),
    ("20+",       pl.col("planned_prep_min") > 20),
]

labels, means, counts = [], [], []
for label, filt in buckets:
    s = both_full.filter(filt)
    labels.append(label)
    means.append(s["start_delay_min"].mean())
    counts.append(s.shape[0])

# --- Layout: density | density | diverging bar ---
fig = plt.figure(figsize=(20, 4.5))
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 0.7], wspace=0.12)

ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1], sharey=ax1)
ax3 = fig.add_subplot(gs[2])

# === Panel 1: aggregate ===
y_all = kde_all(x_grid)
ax1.fill_between(x_grid, y_all, alpha=0.35, color="#888888")
ax1.plot(x_grid, y_all, color="#666666", linewidth=1.5)

# Use unfiltered means for annotations (match poster_analysis.md)
mean_all_full = both_full["start_delay_min"].mean()
mean_zero_full = both_full.filter(pl.col("planned_prep_min") == 0)["start_delay_min"].mean()
mean_has_full = both_full.filter(pl.col("planned_prep_min") > 0)["start_delay_min"].mean()

y_all = kde_all(x_grid)
ax1.axvline(mean_all_full, color=DARK, linewidth=1.5, linestyle="--", zorder=4)
ax1.text(mean_all_full + 3, y_all.max() * 0.75, f"mean = {mean_all_full:.1f} min",
         fontsize=10, fontweight="bold", color=DARK, va="center")

ax1.set_title("All surgeries", fontsize=13, fontweight="bold",
              color=DARK, loc="left", pad=8)
ax1.text(0.97, 0.93, f"n = {total:,}",
         transform=ax1.transAxes, ha="right", va="top",
         fontsize=9, color="#888888")

# === Panel 2: split ===
y_zero = kde_zero(x_grid) * frac_zero
y_has = kde_has(x_grid) * frac_has

ax2.fill_between(x_grid, y_zero, alpha=0.4, color=RED,
                 label="No prep allocated (81%)")
ax2.plot(x_grid, y_zero, color=RED, linewidth=1.5)
ax2.fill_between(x_grid, y_has, alpha=0.4, color=TEAL,
                 label="Prep allocated (19%)")
ax2.plot(x_grid, y_has, color=TEAL, linewidth=1.5)

y_peak = max(y_zero.max(), y_has.max())

ax2.axvline(mean_zero_full, color=RED, linewidth=1.5, linestyle="--", zorder=4)
ax2.text(mean_zero_full + 2, y_peak * 0.82, f"+{mean_zero_full:.1f} min",
         fontsize=10, fontweight="bold", color=RED)

ax2.axvline(mean_has_full, color=TEAL, linewidth=1.5, linestyle="--", zorder=4)
mean_has_label = f"{mean_has_full:+.1f} min"
ax2.text(mean_has_full - 2, y_peak * 0.68, mean_has_label,
         fontsize=10, fontweight="bold", color=TEAL, ha="right")

import matplotlib.lines as mlines
legend_mean = mlines.Line2D([], [], color=DARK, linewidth=1.5, linestyle="--", label="Group mean")

ax2.set_title("Split by prep allocation", fontsize=13, fontweight="bold",
              color=DARK, loc="left", pad=8)
ax2.legend(handles=[*ax2.get_legend_handles_labels()[0], legend_mean],
           labels=[*ax2.get_legend_handles_labels()[1], "Group mean"],
           loc="upper right", fontsize=8.5, frameon=False)


# === Panel 3: vertical diverging bar ===
x_pos = np.arange(len(labels))
bar_w = 0.55
colors = [RED if m > 0 else TEAL for m in means]

ax3.bar(x_pos, means, color=colors, width=bar_w, edgecolor="none", zorder=2)
ax3.axhline(0, color="#444444", linewidth=1.0, zorder=3)

for i, (mean, count) in enumerate(zip(means, counts)):
    pad = 1.2
    va = "bottom" if mean > 0 else "top"
    y_text = mean + pad if mean > 0 else mean - pad
    ax3.text(i, y_text, f"{mean:+.1f}",
             ha="center", va=va, fontsize=10, fontweight="bold", color=colors[i])
    pct = count / total * 100
    pct_str = f"{pct:.0f}%" if pct > 5 else f"{pct:.1f}%"
    y_n = -15 if mean > 0 else max(mean - 5, -15)
    ax3.text(i, -14.5, pct_str, ha="center", va="top",
             fontsize=8.5, color="#888888")

ax3.set_xticks(x_pos)
ax3.set_xticklabels(labels, fontsize=9, fontweight="600")
ax3.set_ylim(-16, 32)
ax3.set_ylabel("Mean start delay (min)", fontsize=10, color=MUTED)
ax3.set_title("By prep bucket", fontsize=13, fontweight="bold",
              color=DARK, loc="left", pad=8)

ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.spines["bottom"].set_visible(False)
ax3.tick_params(bottom=False)
ax3.yaxis.grid(True, color="#e8e8e8", linewidth=0.5, zorder=0)
ax3.set_axisbelow(True)
ax3.tick_params(axis="y", colors="#888888")
ax3.spines["left"].set_color("#cccccc")

# === Shared density styling ===
for ax in (ax1, ax2):
    ax.set_xlabel("Start delay (minutes)", fontsize=10, color=MUTED)
    ax.axvline(0, color="#cccccc", linewidth=0.8, zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(left=False, labelleft=False)
    ax.tick_params(axis="x", colors="#888888")
    ax.spines["bottom"].set_color("#cccccc")
    ax.set_xlim(-60, 120)

plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
print(f"All: mean={mean_all_full:.1f}, n={total:,}")
print(f"Zero prep: mean={mean_zero_full:.1f}")
print(f"Has prep: mean={mean_has_full:.1f}")
