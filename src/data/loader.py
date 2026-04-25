"""
Loads the two raw CSV files (completed and cancelled operations) into Polars DataFrames.

Column names are translated from Danish to English snake_case. Values are left as-is in Danish.
"""

import re
from pathlib import Path

import polars as pl

from utils.logger import get_logger


logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"

_DATETIME_FMT = "%Y-%m-%d %H:%M:%S,%3f"

_CORE_RENAME_COMPLETED: dict[str, str] = {
    "Case-ID Anonymous": "case_id",
    "Patient Alder": "patient_age",
    "Speciale": "specialty",
    "Stue": "or_room",
    "Operationsgang ID": "or_hallway_id",
    "Akut case (J/N)": "is_acute",
    "Dato": "date",
    "Pt ankommet til hospitalet": "ts_patient_arrived",
    "Planlagt stue klargøring start": "ts_or_prep_planned_start",
    "Stue klargøring start": "ts_or_prep_start",
    "Stue klargjort": "ts_or_prep_done",
    "Patient på stuen (Planlagt)": "ts_patient_in_or_planned",
    "Patient på stuen": "ts_patient_in_or",
    "Anæstesistart": "ts_anesthesia_start",
    "Anæstesi melder klar": "ts_anesthesia_ready",
    "Procedure start": "ts_procedure_start",
    "Procedure slut": "ts_procedure_end",
    "Patient klar til afgang": "ts_patient_ready_to_leave",
    "Patient forlader stuen (Planlagt)": "ts_patient_leaves_or_planned",
    "Patient forlader stuen": "ts_patient_leaves_or",
    "Stue rengjort (Planlagt)": "ts_or_cleaned_planned",
    "Stue rengøring start": "ts_or_cleaning_start",
    "Stue rengjort": "ts_or_cleaned",
    "I opvågning": "ts_recovery_start",
    "Anæstesistop": "ts_anesthesia_end",
    "Klar til udskrivelse efter opvågning": "ts_ready_for_discharge",
    "Patient forlader afdeling": "ts_patient_discharged",
    "Forsinkelse (minutter)": "delay_minutes",
    "Overskredet (minutter)": "overtime_minutes",
    "Forsinkelsesårsag": "delay_reason",
    "Procedure - Tekst & ID": "procedure_text_id",
    "Aktionsdiagnose - Kode & tekst": "diagnosis_code_text",
    "Aktionsdiagnose - Gruppe": "diagnosis_group",
}

_CORE_RENAME_CANCELLED: dict[str, str] = {
    "Case-ID Anonymous": "case_id",
    "Dato og tid": "scheduled_datetime",
    "Primær procedure - Tekst": "primary_procedure",
    "Aflyst efter operationsprogrammet er afsluttet?": "cancelled_after_program_planned",
    "Aflyst på dagen for operationen? ": "cancelled_on_day_of_surgery",
    "Aflysningsårsag": "cancellation_reason",
    "Forventet varighed (min.)": "expected_duration_min",
    "Ombooket": "is_rebooked",
    "Stue": "or_room",
    "Operationsgang ID": "or_hallway_id",
}

_DATETIME_COLS_COMPLETED = [
    "ts_patient_arrived",
    "ts_or_prep_planned_start",
    "ts_or_prep_start",
    "ts_or_prep_done",
    "ts_patient_in_or_planned",
    "ts_patient_in_or",
    "ts_anesthesia_start",
    "ts_anesthesia_ready",
    "ts_procedure_start",
    "ts_procedure_end",
    "ts_patient_ready_to_leave",
    "ts_patient_leaves_or_planned",
    "ts_patient_leaves_or",
    "ts_or_cleaning_start",
    "ts_or_cleaned_planned",
    "ts_or_cleaned",
    "ts_recovery_start",
    "ts_anesthesia_end",
    "ts_ready_for_discharge",
    "ts_patient_discharged",
]


def _clean_suffix(name: str) -> str:
    """Transliterate Danish chars and convert to snake_case ASCII."""
    name = name.translate(str.maketrans("æøåÆØÅ", "eoaEOA"))
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def _build_staff_resource_rename(columns: list[str]) -> dict[str, str]:
    rename: dict[str, str] = {}
    for col in columns:
        stripped = col.strip()
        if stripped.startswith("Staff."):
            rename[col] = "staff_" + _clean_suffix(stripped[len("Staff.") :])
        elif stripped.startswith("Ressource."):
            rename[col] = "resource_" + _clean_suffix(stripped[len("Ressource.") :])
    return rename


def load_completed() -> pl.DataFrame:
    df = pl.read_csv(
        DATA_DIR / "completed_operations.csv",
        separator=";",
        infer_schema_length=10000,
        null_values=[""],
    )

    df = df.rename(
        {**_CORE_RENAME_COMPLETED, **_build_staff_resource_rename(df.columns)}
    )

    df = df.with_columns(
        [
            pl.col(c).str.strptime(pl.Datetime, format=_DATETIME_FMT, strict=False).dt.cast_time_unit("us")
            for c in _DATETIME_COLS_COMPLETED
        ]
        + [
            pl.col("date")
            .str.strptime(pl.Datetime, format=_DATETIME_FMT, strict=False)
            .cast(pl.Date)
        ]
        + [pl.col("is_acute").eq("Ja")]
    )

    bool_cols = [
        c for c in df.columns if c.startswith("staff_") or c.startswith("resource_")
    ]
    df = df.with_columns(
        [pl.col(c).cast(pl.Int8, strict=False).cast(pl.Boolean) for c in bool_cols]
    )

    return df


def load_cancelled() -> pl.DataFrame:
    df = pl.read_csv(
        DATA_DIR / "cancelled_operations.csv",
        separator=";",
        infer_schema_length=10000,
        null_values=[""],
    )

    df = df.rename(_CORE_RENAME_CANCELLED)

    df = df.with_columns(
        [
            pl.col("scheduled_datetime").str.strptime(
                pl.Datetime, format=_DATETIME_FMT, strict=False
            ).dt.cast_time_unit("us"),
            pl.col("cancelled_after_program_planned").eq("Ja"),
            pl.col("cancelled_on_day_of_surgery").eq("Ja"),
            pl.col("is_rebooked").eq("Ja"),
        ]
    )

    return df


if __name__ == "__main__":
    try:
        logger.info("Loading completed operations...")
        completed = load_completed()
        logger.success(f"Completed operations loaded. Shape: {completed.shape}")
        logger.info(f"Schema:\n{completed.schema}")
    except Exception as e:
        logger.error(f"Failed to load completed operations: {e}")

    try:
        logger.info("Loading cancelled operations...")
        cancelled = load_cancelled()
        logger.success(f"Cancelled operations loaded. Shape: {cancelled.shape}")
        logger.info(f"Schema:\n{cancelled.schema}")
    except Exception as e:
        logger.error(f"Failed to load cancelled operations: {e}")
