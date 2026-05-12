"""Generate the 'Problem' panel chart: diverging horizontal bar chart."""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from data.loader import load_completed

RED = "#c0392b"
TEAL = "#1a8a7d"
OUT = "poster/problem_v1_diverging_bar.png"

df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_patient_in_or_planned") - pl.col("ts_or_prep_planned_start"))
     .dt.total_seconds() / 60).alias("planned_prep_min"),
    ((pl.col("ts_patient_in_or") - pl.col("ts_patient_in_or_planned"))
     .dt.total_seconds() / 60).alias("start_delay_min"),
])

both = df.filter(
    pl.col("planned_prep_min").is_not_null()
    & pl.col("start_delay_min").is_not_null()
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
    means.append(s["start_delay_min"].mean())
    counts.append(s.shape[0])

# --- Plot ---
fig, ax = plt.subplots(figsize=(16, 4.5))

y_pos = np.arange(len(labels))
bar_height = 0.52
colors = [RED if m > 0 else TEAL for m in means]

ax.barh(y_pos, means, color=colors, height=bar_height, edgecolor="none", zorder=2)
ax.axvline(x=0, color="#444444", linewidth=1.0, zorder=3)

for i, (mean, count) in enumerate(zip(means, counts)):
    pad = 0.8
    ha = "left" if mean > 0 else "right"
    x_text = mean + pad if mean > 0 else mean - pad
    ax.text(x_text, i, f"{mean:+.1f} min", va="center", ha=ha,
            fontsize=13, fontweight="bold", color=colors[i])

    pct = count / total * 100
    n_str = (f"n = {count:,}  ({pct:.0f}%)" if pct > 5
             else f"n = {count:,}  ({pct:.1f}%)")
    ax.text(34, i, n_str, va="center", ha="left", fontsize=10, color="#888888")

ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=14, fontweight="600")
ax.invert_yaxis()

ax.set_xlim(-14, 33)
ax.set_xlabel("Mean start delay (minutes)", fontsize=12, color="#555555")
ax.text(0.3, len(labels) - 0.3, "Planned\nstart",
        va="top", ha="left", fontsize=9, color="#666666", style="italic")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False, axis="y")
ax.tick_params(axis="x", colors="#888888")
ax.spines["bottom"].set_color("#cccccc")
ax.xaxis.grid(True, color="#e8e8e8", linewidth=0.5, zorder=0)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
