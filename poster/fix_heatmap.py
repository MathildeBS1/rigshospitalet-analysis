"""Panel 2b: 64-cell lookup table heatmap (specialty × anesthesia), truncated."""

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from data.loader import load_completed

TEAL = "#1a6b5a"
DARK = "#333333"
MUTED = "#555555"
BREAK_COLOR = "#f5f5f5"

N_SHOW = 5
OUT = "poster/fix_heatmap.png"

TRANSLATE = {
    "Alloplastik": "Arthroplasty",
    "Anæstesiologi": "Anesthesiology",
    "Brystkirurgi": "Breast surgery",
    "Børnekirurgi": "Pediatric surgery",
    "Børneortopædi": "Pediatric orthopedics",
    "Gynækologi": "Gynecology",
    "Gynækologi-obstetrik": "Gynecology-obstetrics",
    "Hjertekirurgi": "Cardiac surgery",
    "Håndkirurgi": "Hand surgery",
    "Hæmatologi": "Hematology",
    "Hæmatologi-Onkologi pædiatrisk": "Pediatric hemato-oncology",
    "Kardiologi": "Cardiology",
    "Karkirurgi": "Vascular surgery",
    "Kirurgi": "General surgery",
    "Lungesygdomme": "Pulmonology",
    "Medicinsk gastroenterologi": "Gastroenterology",
    "Nefrologi": "Nephrology",
    "Neurokirurgi": "Neurosurgery",
    "Neurologi": "Neurology",
    "Obstetrik": "Obstetrics",
    "Onkologi": "Oncology",
    "Ortopædkirurgi": "Orthopedic surgery",
    "Plastikkirurgi": "Plastic surgery",
    "Pædiatri": "Pediatrics",
    "Rygkirurgi": "Spine surgery",
    "Tand- mund- og kæbekirurgi": "Oral & maxillofacial",
    "Thoraxkirurgi": "Thoracic surgery",
    "Traumeortopædi": "Trauma orthopedics",
    "Tumorortopædi": "Tumor orthopedics",
    "Urologi": "Urology",
    "Øjenkirurgi": "Ophthalmology",
    "Øre-næse-hals": "ENT",
}

df = load_completed().unique(subset=["case_id"], keep="first")
df = df.with_columns([
    ((pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
     .dt.total_seconds() / 60).alias("w2"),
    pl.col("ts_anesthesia_start").is_not_null().alias("has_anesthesia"),
])

w2 = df.filter(
    pl.col("w2").is_not_null()
    & pl.col("w2").is_between(0, 240)
    & pl.col("specialty").is_not_null()
)

lookup = (
    w2.group_by(["specialty", "has_anesthesia"])
    .agg([
        pl.col("w2").mean().alias("mean_w2"),
        pl.len().alias("n"),
    ])
)

pivot = lookup.pivot(on="has_anesthesia", index="specialty", values="mean_w2")

col_true = "true" if "true" in pivot.columns else "True" if "True" in pivot.columns else None
col_false = "false" if "false" in pivot.columns else "False" if "False" in pivot.columns else None

if col_true is None or col_false is None:
    print("Columns:", pivot.columns)
    raise ValueError("Could not find anesthesia columns")

pivot = pivot.with_columns([
    pl.col(col_false).alias("no_anes"),
    pl.col(col_true).alias("with_anes"),
])

combined = pivot.select(["specialty", "no_anes", "with_anes"])
combined = combined.sort("specialty")

specialties = [TRANSLATE.get(s, s) for s in combined["specialty"].to_list()]
no_anes_vals = combined["no_anes"].to_numpy()
with_anes_vals = combined["with_anes"].to_numpy()

top_specs = specialties[:N_SHOW]
bot_specs = specialties[-N_SHOW:]
top_no = no_anes_vals[:N_SHOW]
top_with = with_anes_vals[:N_SHOW]
bot_no = no_anes_vals[-N_SHOW:]
bot_with = with_anes_vals[-N_SHOW:]

n_hidden = len(specialties) - 2 * N_SHOW
break_label = f"⋮  {n_hidden} more  ⋮"

display_specs = top_specs + [""] + bot_specs
display_no = np.concatenate([top_no, [np.nan], bot_no])
display_with = np.concatenate([top_with, [np.nan], bot_with])
data = np.column_stack([display_no, display_with])
break_row = N_SHOW

vmin = np.nanmin(data)
vmax = np.nanmax(data)

n_rows = len(display_specs)
fig, ax = plt.subplots(figsize=(8, 8))

cmap_teal = mcolors.LinearSegmentedColormap.from_list(
    "teal", ["#f0f9f6", "#c2e0d8", "#6bb5a0", TEAL, "#0e3d30"])
im = ax.imshow(data, aspect="auto", cmap=cmap_teal, interpolation="nearest",
               vmin=vmin, vmax=vmax)

ax.add_patch(plt.Rectangle((-0.5, break_row - 0.5), 2, 1,
             facecolor=BREAK_COLOR, edgecolor="none", zorder=3))
ax.text(0.5, break_row, break_label, ha="center", va="center",
        fontsize=9, color="#999999", style="italic", zorder=4)

for i in range(n_rows):
    if i == break_row:
        continue
    for j, val in enumerate([display_no[i], display_with[i]]):
        if np.isnan(val):
            ax.text(j, i, "—", ha="center", va="center", fontsize=10, color="#999999")
        else:
            color = "white" if val > 40 else DARK
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=10, fontweight="bold", color=color)

ax.set_xticks([0, 1])
ax.set_xticklabels(["No anesthesia", "With anesthesia"], fontsize=12, fontweight="600")
ax.xaxis.tick_top()
ax.set_yticks(range(n_rows))
ax.set_yticklabels(display_specs, fontsize=10)
ax.tick_params(left=False, top=False)

cbar = fig.colorbar(im, ax=ax, shrink=0.4, pad=0.02)
cbar.set_label("Mean prep time (min)", fontsize=10, color=MUTED)
cbar.ax.tick_params(labelsize=9)

ax.spines[:].set_visible(False)

plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUT}")
print(f"Showing {N_SHOW} top + {N_SHOW} bottom of {len(specialties)} specialties")
