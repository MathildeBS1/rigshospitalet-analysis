"""
EDA 5: Patient-Side Prep Time & Complexity

Measures ts_patient_in_or → ts_procedure_start (patient enters OR → knife time).
This is the cleanest prep window: 99.4% coverage, real distribution, officially
defined as patient arriving at OR to first procedure beginning.

Avoids ts_or_prep_start → ts_or_prep_done (62% same-timestamp, unusable).

Questions:
  1. How long is patient-side prep, and does it differ by anesthesia?
  2. Do staff count and equipment count predict patient-side prep time?
  3. Does the planned schedule account for this complexity signal?
"""

import polars as pl

from data.loader import load_completed
from utils.logger import get_logger

logger = get_logger(__name__)

PREP_MIN_FILTER = (0, 240)  # exclude obvious data errors
PLANNED_INOR_FILTER = (0, 600)
MIN_CASES_PER_PROCEDURE = 50


def _build_features(cases: pl.DataFrame) -> pl.DataFrame:
    staff_cols = [c for c in cases.columns if c.startswith("staff_")]
    resource_cols = [c for c in cases.columns if c.startswith("resource_")]

    return cases.with_columns([
        (pl.col("ts_procedure_start") - pl.col("ts_patient_in_or"))
        .dt.total_minutes()
        .alias("patient_prep_min"),

        (pl.col("ts_patient_leaves_or_planned") - pl.col("ts_patient_in_or_planned"))
        .dt.total_minutes()
        .alias("planned_inor_min"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in staff_cols])
        .alias("staff_count"),

        pl.sum_horizontal([pl.col(c).cast(pl.Int8, strict=False) for c in resource_cols])
        .alias("resource_count"),

        pl.col("ts_anesthesia_start").is_not_null().alias("has_anesthesia"),
    ])


def run(specialty: str | None = None) -> None:
    logger.info("Loading completed operations...")
    df = load_completed()

    if specialty:
        df = df.filter(pl.col("specialty") == specialty)
        logger.info(f"Filtered to specialty: {specialty}")

    cases = df.unique(subset=["case_id"], keep="first")
    cases = _build_features(cases)
    logger.info(f"Unique cases: {cases.shape[0]:,}")

    valid = cases.filter(
        pl.col("patient_prep_min").is_between(*PREP_MIN_FILTER),
        pl.col("ts_patient_in_or").is_not_null(),
        pl.col("ts_procedure_start").is_not_null(),
    )
    logger.info(f"Cases with valid patient-side prep: {valid.shape[0]:,}")

    # ── 1. Overall distribution ──────────────────────────────────────────────
    logger.info("\n── Patient-side prep distribution (ts_patient_in_or → ts_procedure_start) ──")
    print(valid.select(
        pl.col("patient_prep_min").mean().round(1).alias("mean"),
        pl.col("patient_prep_min").median().round(1).alias("median"),
        pl.col("patient_prep_min").quantile(0.25).round(1).alias("p25"),
        pl.col("patient_prep_min").quantile(0.75).round(1).alias("p75"),
        pl.col("patient_prep_min").quantile(0.90).round(1).alias("p90"),
    ))

    # ── 2. Anesthesia vs non-anesthesia ─────────────────────────────────────
    logger.info("\n── Patient-side prep by anesthesia ──")
    print(
        valid.group_by("has_anesthesia")
        .agg(
            pl.col("patient_prep_min").mean().round(1).alias("mean_prep_min"),
            pl.col("patient_prep_min").median().round(1).alias("median_prep_min"),
            pl.len().alias("n_cases"),
        )
        .sort("has_anesthesia")
    )

    # ── 3. Complexity correlations (procedure level, n >= 50) ────────────────
    logger.info(f"\n── Complexity correlations at procedure level (n >= {MIN_CASES_PER_PROCEDURE}) ──")

    proc = (
        valid.filter(
            pl.col("procedure_text_id").is_not_null(),
            pl.col("staff_count").is_not_null(),
            pl.col("resource_count").is_not_null(),
            pl.col("planned_inor_min").is_between(*PLANNED_INOR_FILTER),
        )
        .group_by("procedure_text_id")
        .agg(
            pl.len().alias("n"),
            pl.col("patient_prep_min").mean().alias("mean_prep"),
            pl.col("planned_inor_min").mean().alias("mean_planned_inor"),
            pl.col("staff_count").mean().alias("mean_staff"),
            pl.col("resource_count").mean().alias("mean_resources"),
        )
        .filter(pl.col("n") >= MIN_CASES_PER_PROCEDURE)
    )

    logger.info(f"Procedures with n >= {MIN_CASES_PER_PROCEDURE}: {proc.shape[0]}")

    r_staff_prep     = proc.select(pl.corr("mean_staff",     "mean_prep")).item()
    r_resource_prep  = proc.select(pl.corr("mean_resources", "mean_prep")).item()
    r_staff_planned  = proc.select(pl.corr("mean_staff",     "mean_planned_inor")).item()
    r_resource_planned = proc.select(pl.corr("mean_resources", "mean_planned_inor")).item()

    logger.info("Actual patient-side prep vs complexity:")
    logger.info(f"  staff_count    r = {r_staff_prep:+.2f}")
    logger.info(f"  resource_count r = {r_resource_prep:+.2f}")
    logger.info("Planned in-OR duration vs complexity (scheduling signal):")
    logger.info(f"  staff_count    r = {r_staff_planned:+.2f}")
    logger.info(f"  resource_count r = {r_resource_planned:+.2f}")

    # ── 4. Specialty breakdown ───────────────────────────────────────────────
    logger.info("\n── Patient-side prep by specialty (min 100 cases) ──")
    by_specialty = (
        valid.group_by("specialty")
        .agg(
            pl.col("patient_prep_min").mean().round(1).alias("mean_prep_min"),
            pl.col("patient_prep_min").median().round(1).alias("median_prep_min"),
            pl.col("staff_count").mean().round(1).alias("mean_staff_count"),
            pl.col("resource_count").mean().round(1).alias("mean_resource_count"),
            pl.len().alias("n_cases"),
        )
        .filter(pl.col("n_cases") >= 100)
        .sort("mean_prep_min", descending=True)
    )
    print(by_specialty)


if __name__ == "__main__":
    import sys
    run(specialty=sys.argv[1] if len(sys.argv) > 1 else None)
