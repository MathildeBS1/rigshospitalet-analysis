"""
Rigshospitalet OR Scheduling Analysis — A1 Exam Poster (DTU Style)
Course: From Analytics to Action (42577), Spring 2026

Run:  python poster/build_poster.py
Out:  poster/rigshospitalet_poster.pdf  (A1 portrait, 300 DPI, print-ready)
"""

import os, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from PIL import Image
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(BASE, "..", "eda", "mathilde",
                      "prep-complexity-gap", "presentation")

def chart(n): return os.path.join(CHARTS, f"{n}.png")

# TODO: set to Linus's chart path once available
SURGERY_CHART = None

# DTU logo: official White_CMYK.png (RGBA, 1951×2846)
DTU_LOGO_WHITE = os.path.join(BASE, "..", "White_CMYK.png")

OUT_PDF = os.path.join(BASE, "rigshospitalet_poster.pdf")

# ── Palette ───────────────────────────────────────────────────────────────────
DTU_RED  = "#990000"
TEAL     = "#1A6B5A"
BG       = "#FFFFFF"
PANEL    = "#F5F5F5"
BORDER   = "#CCCCCC"
DARK     = "#1A202C"
MUTED    = "#555555"

# ── Team ──────────────────────────────────────────────────────────────────────
TEAM = [
    ("Linus Juni",                       "s225224"),
    ("Theodor Dornonville de la Cour",   "s225093"),
    ("Mathilde Sørensen",                "s254124"),
    ("Jose Luis Escobedo Diaz",          "S257410"),
    ("Rune Isaksen",                     "s260390"),
    ("Alexander Sucur",                  "s257222"),
]

# ── Figure constants ───────────────────────────────────────────────────────────
FIG_W, FIG_H = 23.39, 33.11
HDR = 0.180   # red header fraction
FTR = 0.024   # footer fraction

# ── Helpers ───────────────────────────────────────────────────────────────────

def _bg(ax, color=BG):
    ax.set_axis_off()
    ax.add_patch(mpatches.Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=color, edgecolor="none", zorder=0))


def _border(ax, color=BORDER, lw=0.5):
    ax.add_patch(mpatches.Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor="none", edgecolor=color, linewidth=lw, zorder=5))


def show_img(ax, path, placeholder="Chart — to be added", add_border=True):
    _bg(ax, BG)
    img_arr = None
    if path and os.path.exists(path):
        img_arr = np.array(Image.open(path).convert("RGB"))
    if img_arr is not None:
        ax.imshow(img_arr)
        ax.set_aspect("equal")
    else:
        ax.add_patch(mpatches.Rectangle(
            (0.01, 0.01), 0.98, 0.98, transform=ax.transAxes,
            facecolor="#E8E8E8", edgecolor="none"))
        ax.text(0.5, 0.5, placeholder, ha="center", va="center",
                fontsize=9, color="#888", style="italic",
                transform=ax.transAxes, multialignment="center")
    if add_border:
        _border(ax)


def stat_card(ax, number, unit, label, color=DTU_RED, bg="#FEF0F0"):
    _bg(ax, bg)
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.04, 0.04), 0.92, 0.92,
        boxstyle="round,pad=0.015", transform=ax.transAxes,
        facecolor=bg, edgecolor=color, linewidth=1.8, zorder=1))
    ax.text(0.5, 0.63, number, ha="center", va="center",
            fontsize=23, fontweight="bold", color=color,
            transform=ax.transAxes, zorder=2)
    if unit:
        ax.text(0.5, 0.40, unit, ha="center", va="center",
                fontsize=10, fontweight="bold", color=color,
                transform=ax.transAxes, zorder=2)
    ax.text(0.5, 0.18, label, ha="center", va="center",
            fontsize=7.8, color=MUTED, transform=ax.transAxes,
            multialignment="center", zorder=2)


def col_header(ax, text, accent=DTU_RED):
    _bg(ax, accent)
    ax.text(0.5, 0.5, text, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="white",
            transform=ax.transAxes, zorder=1)


def caption_ax(ax, text):
    _bg(ax, BG)
    ax.text(0.5, 0.55, text, ha="center", va="center",
            fontsize=7.8, color=MUTED, style="italic",
            transform=ax.transAxes, multialignment="center", wrap=True)


def text_panel(ax, body, title=None, bg=PANEL, fontsize=8.6, title_color=None):
    """Clean panel: thin top-border strip + title + body. No heavy filled box."""
    if title_color is None:
        title_color = DTU_RED
    _bg(ax, bg)
    # Thin colored accent bar at top
    ax.add_patch(mpatches.Rectangle(
        (0, 0.97), 1, 0.03, transform=ax.transAxes,
        facecolor=title_color, edgecolor="none", zorder=1))
    y = 0.90
    if title:
        ax.text(0.035, y, title, ha="left", va="top",
                fontsize=fontsize + 2.0, fontweight="bold", color=title_color,
                transform=ax.transAxes, zorder=2)
        y -= 0.13
        # Thin rule under title
        ax.add_patch(mpatches.Rectangle(
            (0.035, y + 0.01), 0.930, 0.006, transform=ax.transAxes,
            facecolor=BORDER, edgecolor="none", zorder=2))
        y -= 0.06
    wrapped = "\n".join(
        ("\n".join(textwrap.wrap(ln, 80)) if ln else "")
        for ln in body.splitlines()
    )
    ax.text(0.035, y, wrapped, ha="left", va="top",
            fontsize=fontsize, color=DARK, transform=ax.transAxes,
            linespacing=1.55, zorder=2)


def bullet_panel(ax, title, items, bg=PANEL, fontsize=8.6, title_color=None):
    if title_color is None:
        title_color = DTU_RED
    _bg(ax, bg)
    ax.add_patch(mpatches.Rectangle(
        (0, 0.97), 1, 0.03, transform=ax.transAxes,
        facecolor=title_color, edgecolor="none", zorder=1))
    ax.text(0.035, 0.90, title, ha="left", va="top",
            fontsize=fontsize + 2.0, fontweight="bold", color=title_color,
            transform=ax.transAxes, zorder=2)
    ax.add_patch(mpatches.Rectangle(
        (0.035, 0.72), 0.930, 0.006, transform=ax.transAxes,
        facecolor=BORDER, edgecolor="none", zorder=2))
    # Single text block for clean linespacing
    bullet_lines = []
    for item in items:
        wrapped = textwrap.wrap(item, 82)
        if wrapped:
            bullet_lines.append("→  " + wrapped[0])
            for extra in wrapped[1:]:
                bullet_lines.append("    " + extra)
            bullet_lines.append("")
    ax.text(0.035, 0.68, "\n".join(bullet_lines), ha="left", va="top",
            fontsize=fontsize, color=DARK, transform=ax.transAxes,
            linespacing=1.60, zorder=2)


# ── Build ─────────────────────────────────────────────────────────────────────

def build():
    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG)

    # ══════════════════════════════════════════════════════════════════════════
    # FULL-BLEED HEADER
    # ══════════════════════════════════════════════════════════════════════════
    ax_hdr = fig.add_axes([0, 1 - HDR, 1, HDR])
    _bg(ax_hdr, DTU_RED)

    # DTU logo — top-aligned in header so it doesn't overlap the title
    if os.path.exists(DTU_LOGO_WHITE):
        logo_img = np.array(Image.open(DTU_LOGO_WHITE).convert("RGBA"))
        logo_h_px, logo_w_px = logo_img.shape[:2]
        logo_ar = logo_w_px / logo_h_px
        logo_h_fig = HDR * 0.38                         # 38% of header height
        logo_w_fig = logo_h_fig * logo_ar * (FIG_H / FIG_W)
        logo_b_fig = 1.0 - logo_h_fig - 0.006           # pin to top of header
        ax_logo = fig.add_axes([0.028, logo_b_fig, logo_w_fig, logo_h_fig])
        ax_logo.set_axis_off()
        ax_logo.imshow(logo_img)
        ax_logo.set_aspect("equal")

    # Course + group (top-right, small)
    ax_hdr.text(0.972, 0.93,
                "From Analytics to Action (42577)  ·  DTU Spring 2026",
                ha="right", va="top", fontsize=9, color="white",
                transform=ax_hdr.transAxes)
    ax_hdr.text(0.972, 0.82, "Group 15",
                ha="right", va="top", fontsize=9, color="white",
                transform=ax_hdr.transAxes)

    # Main title — large, LEFT-ALIGNED (DTU template style)
    ax_hdr.text(0.035, 0.52,
                "The Schedule Fails Before Surgery Starts",
                ha="left", va="center",
                fontsize=36, fontweight="bold", color="white",
                transform=ax_hdr.transAxes)

    # Subtitle
    ax_hdr.text(0.035, 0.31,
                "Reducing operating-room delays through better "
                "preparation and surgery time allocation",
                ha="left", va="center",
                fontsize=11.5, color="white",
                transform=ax_hdr.transAxes)

    # Thin white rule
    ax_hdr.add_patch(mpatches.Rectangle(
        (0.035, 0.185), 0.935, 0.003, transform=ax_hdr.transAxes,
        facecolor="white", edgecolor="none", alpha=0.45, zorder=2))

    # Team names
    team_str = "  ·  ".join(f"{n} ({sid})" for n, sid in TEAM)
    ax_hdr.text(0.035, 0.13, team_str,
                ha="left", va="center",
                fontsize=8.0, color="white", alpha=0.88,
                transform=ax_hdr.transAxes)

    # ══════════════════════════════════════════════════════════════════════════
    # FULL-BLEED FOOTER
    # ══════════════════════════════════════════════════════════════════════════
    ax_ftr = fig.add_axes([0, 0, 1, FTR])
    _bg(ax_ftr, DTU_RED)
    ax_ftr.text(0.5, 0.5,
                "From Analytics to Action (42577)  ·  "
                "Technical University of Denmark  ·  Spring 2026",
                ha="center", va="center",
                fontsize=8.5, color="white",
                transform=ax_ftr.transAxes)

    # ══════════════════════════════════════════════════════════════════════════
    # BODY GridSpec  (challenge | col-bar | main | gap | bottom)
    # ══════════════════════════════════════════════════════════════════════════
    BODY_TOP = 1 - HDR - 0.006
    BODY_BOT = FTR + 0.006

    gs = gridspec.GridSpec(
        5, 1, figure=fig,
        left=0.022, right=0.978,
        top=BODY_TOP, bottom=BODY_BOT,
        hspace=0.010,
        height_ratios=[0.044, 0.024, 0.805, 0.012, 0.115],
        #               chal   bar   main  gap   bot
    )

    # ── Challenge banner ───────────────────────────────────────────────────────
    ax_ch = fig.add_subplot(gs[0])
    _bg(ax_ch, "#F8F0F0")
    ax_ch.add_patch(mpatches.Rectangle(
        (0, 0), 0.004, 1, transform=ax_ch.transAxes,
        facecolor=DTU_RED, edgecolor="none", zorder=1))
    _border(ax_ch, "#E0D0D0")
    ax_ch.text(0.016, 0.68,
               "Research question: How accurate are Rigshospitalet's pre-operative scheduling "
               "estimates — and what can be done to improve them?",
               ha="left", va="center", fontsize=10, fontweight="bold", color=DARK,
               transform=ax_ch.transAxes, zorder=2)
    ax_ch.text(0.016, 0.25,
               "Dataset: 120,868 surgical cases  ·  32 specialties  ·  129 OR rooms  ·  2024–2025  ·  "
               "Two independent failures identified: preparation time and surgery duration "
               "(r = −0.01 — separate fixes required)",
               ha="left", va="center", fontsize=8.5, color=MUTED,
               transform=ax_ch.transAxes, zorder=2)

    # ── Column headers ─────────────────────────────────────────────────────────
    gs_bar = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=gs[1], wspace=0.012)
    for i, (lbl, col) in enumerate([
        ("Finding 1 — Preparation Time Allocation", DTU_RED),
        ("Finding 2 — Surgery Duration",             DTU_RED),
        ("The Fix & Patient Impact",                 TEAL),
    ]):
        col_header(fig.add_subplot(gs_bar[i]), lbl, col)

    # ── Main 3-column body ─────────────────────────────────────────────────────
    gs_main = gridspec.GridSpecFromSubplotSpec(
        1, 3, subplot_spec=gs[2], wspace=0.018)

    # ── COLUMN 1: Prep finding ─────────────────────────────────────────────────
    c1 = gridspec.GridSpecFromSubplotSpec(
        8, 1, subplot_spec=gs_main[0],
        hspace=0.015,
        height_ratios=[0.082, 0.275, 0.032, 0.196, 0.032, 0.170, 0.032, 0.181])

    gs_c1s = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=c1[0], wspace=0.012)
    stat_card(fig.add_subplot(gs_c1s[0]),
              "73%", None, "of cases start late", DTU_RED, "#FEF0F0")
    stat_card(fig.add_subplot(gs_c1s[1]),
              "+22.8", "min", "mean prep time gap", DTU_RED, "#FEF0F0")

    show_img(fig.add_subplot(c1[1]), chart("B"))
    caption_ax(fig.add_subplot(c1[2]),
               "Prep gap (+22.8 min) is 3.5× larger than the surgery gap (+6.4 min) — "
               "most of the scheduling error is a preparation problem.")

    show_img(fig.add_subplot(c1[3]), chart("E"))
    caption_ax(fig.add_subplot(c1[4]),
               "Three OR day patterns: cascading (41% — delay grows case-to-case), "
               "recovery (37%), and one-time shock (22%).")

    show_img(fig.add_subplot(c1[5]), chart("F"))
    caption_ax(fig.add_subplot(c1[6]),
               "Complexity signals predict actual prep time (staff r = +0.35, "
               "equipment r = +0.34) but the current schedule ignores them (r ≈ 0).")

    text_panel(fig.add_subplot(c1[7]),
               "Dataset: 120,868 cases (2024–2025), 32 specialties, 129 OR rooms. "
               "66% of prep timestamps were corrupted (identical start/end) and excluded. "
               "Analysis restricted to surgical specialties with clean timestamps: "
               "38,190 final cases. Prep analysis used EDA and a LightGBM model "
               "(2024 train / 2025 test). Surgery analysis used procedure-level "
               "variance decomposition and a lookup table baseline. "
               "The two gaps are uncorrelated (r = −0.01): separate problems, separate fixes.",
               title="Data & Methods")

    # ── COLUMN 2: Surgery finding ──────────────────────────────────────────────
    c2 = gridspec.GridSpecFromSubplotSpec(
        8, 1, subplot_spec=gs_main[1],
        hspace=0.015,
        height_ratios=[0.082, 0.236, 0.032, 0.216, 0.032, 0.240, 0.032, 0.130])

    gs_c2s = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=c2[0], wspace=0.012)
    stat_card(fig.add_subplot(gs_c2s[0]),
              "53.9%", None, "of cases run overtime", DTU_RED, "#FEF0F0")
    stat_card(fig.add_subplot(gs_c2s[1]),
              "+6.4", "min", "mean surgery duration gap", DTU_RED, "#FEF0F0")

    show_img(fig.add_subplot(c2[1]), SURGERY_CHART,
             placeholder="Chart: Surgery duration variance\nby procedure type\n(Linus — to be added)")
    caption_ax(fig.add_subplot(c2[2]),
               "Procedure type alone explains 80.3% of surgery duration variance. "
               "A lookup table resolves most of the gap; ML adds minimal gain.")

    show_img(fig.add_subplot(c2[3]), chart("H"))
    caption_ax(fig.add_subplot(c2[4]),
               "LightGBM feature importance: procedure_code dominates (>2× any other feature), "
               "confirming that a lookup table captures the bulk of the signal.")

    show_img(fig.add_subplot(c2[5]), chart("C"))
    caption_ax(fig.add_subplot(c2[6]),
               "Data pipeline: 133,158 raw rows → 38,190 clean cases after removing "
               "corrupted prep timestamps and deduplicating by case ID.")

    text_panel(fig.add_subplot(c2[7]),
               "The two scheduling failures are statistically independent: "
               "the correlation between the prep gap and the surgery gap is r = −0.01. "
               "Being wrong about preparation time provides no signal about being "
               "wrong about surgery duration, and vice versa. "
               "This means a single 'better forecasting model' cannot fix both — "
               "two separate interventions are required.",
               title="Key finding: two independent failures")

    # ── COLUMN 3: Fix & Impact ─────────────────────────────────────────────────
    c3 = gridspec.GridSpecFromSubplotSpec(
        8, 1, subplot_spec=gs_main[2],
        hspace=0.015,
        height_ratios=[0.082, 0.111, 0.202, 0.032, 0.210, 0.032, 0.211, 0.120])

    gs_c3s = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=c3[0], wspace=0.012)
    stat_card(fig.add_subplot(gs_c3s[0]),
              "22.4", "min", "avg patient wait saved\nper case", TEAL, "#E6F3F0")
    stat_card(fig.add_subplot(gs_c3s[1]),
              "1,154", "hrs", "total wait time saved\nin 2-month test", TEAL, "#E6F3F0")

    text_panel(fig.add_subplot(c3[1]),
               "A LightGBM model (2024 train → 2025 test) eliminates the 22-minute "
               "systematic prep bias and cuts MAE from 23.1 → 14.7 min. "
               "It learns that first-of-day cases need ~twice the prep time "
               "of later cases — a pattern the current schedule ignores entirely.",
               bg="#E6F3F0", fontsize=7.9, title_color=TEAL)

    # Gantt pair — I and J side by side
    gs_gantt = gridspec.GridSpecFromSubplotSpec(
        1, 2, subplot_spec=c3[2], wspace=0.012)
    show_img(fig.add_subplot(gs_gantt[0]), chart("I"))
    show_img(fig.add_subplot(gs_gantt[1]), chart("J"))

    caption_ax(fig.add_subplot(c3[3]),
               "Same OR day, same surgeries. Current schedule (left): 0 min prep → "
               "cascade of 30, 62, 64 min delays. Model (right): 7, 23, 8 min delays.")

    show_img(fig.add_subplot(c3[4]), chart("G"))
    caption_ax(fig.add_subplot(c3[5]),
               "Mean gap: +22.2 → −0.4 min (bias eliminated). "
               "MAE: 23.1 → 14.7 min. R²: −0.69 → +0.19. Tested on unseen 2025 data.")

    show_img(fig.add_subplot(c3[6]), chart("L"))

    text_panel(fig.add_subplot(c3[7]),
               "Applied to a 2-month test window (3,086 cases): patient waiting "
               "time drops from 103,312 to 34,072 minutes — a reduction of 1,154 hours. "
               "Average saving: 22.4 minutes per patient. "
               "No additional resources are required; only the schedule changes.",
               title="Patient impact", title_color=TEAL)

    # ── Gap row ────────────────────────────────────────────────────────────────
    ax_gap = fig.add_subplot(gs[3])
    _bg(ax_gap, "#DEDEDE")

    # ── Bottom: Reflections | Recommendations ─────────────────────────────────
    gs_bot = gridspec.GridSpecFromSubplotSpec(
        1, 2, subplot_spec=gs[4], wspace=0.018)

    text_panel(fig.add_subplot(gs_bot[0]),
               "The problem is ironic: the scheduling system already captures the "
               "timestamps it needs to improve itself, yet 66% are corrupted because "
               "staff record start and end at the same moment — a recording habit, "
               "not a technical failure. Datafication creates infrastructure for "
               "insight, but only if data capture is disciplined. Fixing timestamp "
               "recording (a training or UX prompt, not an infrastructure overhaul) "
               "would double the usable dataset and extend analysis to currently "
               "excluded specialties. The schedule is already datafied; it simply "
               "does not use its own data.",
               title="Reflections on Datafication")

    bullet_panel(fig.add_subplot(gs_bot[1]),
                 "Recommendations",
                 [
                     "Immediately — deploy a procedure-level lookup table for both "
                     "prep and surgery duration allocation. No technology required; "
                     "dramatic improvement from existing data alone.",
                     "Fix timestamp recording — a staff training initiative or a "
                     "system UX prompt, not an infrastructure overhaul. Doubles the "
                     "usable dataset and extends coverage to all specialties.",
                     "Collect surgeon identity and patient ASA score to push model "
                     "accuracy toward R² ≈ 0.90+ and extend to all 32 specialties.",
                 ])

    # ── Save ───────────────────────────────────────────────────────────────────
    fig.savefig(OUT_PDF, format="pdf", dpi=300,
                bbox_inches="tight", facecolor=BG)
    print(f"Saved → {OUT_PDF}")


if __name__ == "__main__":
    build()
