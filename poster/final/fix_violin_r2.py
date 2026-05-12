"""Panel 2a: Violin plot (anesthesia split) + R² comparison bars."""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from data.loader import load_completed

BLUE = "#2c6faa"
AMBER = "#d4910a"
PURPLE = "#7B5EA7"
GRAY = "#cccccc"
DARK = "#333333"

OUT = "poster/fix_violin_r2.png"

df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
     .dt.total_seconds() / 60).alias("w2"),
    pl.col("ts_anesthesia_start").is_not_null().alias("has_anesthesia"),
])

w2 = df.filter(pl.col("w2").is_not_null() & pl.col("w2").is_between(0, 240))

anes = w2.filter(pl.col("has_anesthesia"))["w2"].to_numpy()
no_anes = w2.filter(~pl.col("has_anesthesia"))["w2"].to_numpy()

# --- Layout: violin (dominant) + R² bars (compact) ---
fig = plt.figure(figsize=(8, 8))
gs = gridspec.GridSpec(1, 2, width_ratios=[2.5, 1], wspace=0.35)

# === Violin ===
ax_v = fig.add_subplot(gs[0])

parts = ax_v.violinplot([no_anes, anes], positions=[0, 1], showmedians=False,
                        showextrema=False, widths=0.7)

for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(BLUE if i == 0 else AMBER)
    pc.set_alpha(0.6)
    pc.set_edgecolor("none")

for i, data in enumerate([no_anes, anes]):
    med = np.median(data)
    mean = np.mean(data)
    ax_v.scatter(i, mean, color="white", edgecolor=DARK, s=60, zorder=5, linewidth=1.5)
    ax_v.hlines(med, i - 0.15, i + 0.15, color=DARK, linewidth=2, zorder=5)


ax_v.text(0, -12, f"n = {len(no_anes):,}", ha="center", fontsize=10, color="#888888")
ax_v.text(1, -12, f"n = {len(anes):,}", ha="center", fontsize=10, color="#888888")

ax_v.set_xticks([0, 1])
ax_v.set_xticklabels(["No anesthesia", "With anesthesia"], fontsize=13, fontweight="600")
ax_v.set_ylabel("Patient prep time (minutes)", fontsize=12, color="#555555")
ax_v.set_ylim(-18, 140)
ax_v.spines["top"].set_visible(False)
ax_v.spines["right"].set_visible(False)
ax_v.spines["bottom"].set_visible(False)
ax_v.tick_params(bottom=False)
ax_v.yaxis.grid(True, color="#e8e8e8", linewidth=0.5)
ax_v.set_axisbelow(True)

# === R² vertical bars ===
ax_r = fig.add_subplot(gs[1])

targets = ["Lookup\ntable", "ML\nmodel"]
r2_vals = [0.576, 0.699]

x_pos = np.array([0, 0.6])
ax_r.bar(x_pos, [1.0, 1.0], width=0.45, color="#f0f0f0", edgecolor="none", zorder=1)
ax_r.bar(x_pos, r2_vals, width=0.45, color=PURPLE, edgecolor="none", zorder=2)

for i, val in enumerate(r2_vals):
    ax_r.text(x_pos[i], val + 0.03, f"{val:.3f}", ha="center", va="bottom",
              fontsize=11, fontweight="bold", color=PURPLE)

ax_r.set_xticks(x_pos)
ax_r.set_xticklabels(targets, fontsize=10, fontweight="600")
ax_r.set_ylim(0, 1.0)
ax_r.set_ylabel("R²", fontsize=11, color="#555555")

ax_r.spines["top"].set_visible(False)
ax_r.spines["right"].set_visible(False)
ax_r.spines["bottom"].set_visible(False)
ax_r.tick_params(bottom=False)
ax_r.yaxis.grid(True, color="#e8e8e8", linewidth=0.5)
ax_r.set_axisbelow(True)

import matplotlib.lines as mlines
legend_dot = mlines.Line2D([], [], marker="o", color="white", markeredgecolor=DARK,
                           markersize=8, markeredgewidth=1.5, linestyle="None", label="Mean")
legend_line = mlines.Line2D([], [], color=DARK, linewidth=2, linestyle="-", label="Median")
ax_v.legend(handles=[legend_dot, legend_line], loc="upper left", fontsize=10,
            frameon=False, handletextpad=0.4)

plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
