"""
Parses an uploaded meter CSV into a list of (timestamp, kwh) tuples.

Expected format (flexible column names, case-insensitive):
    timestamp, kwh
    2026-08-01T00:00:00, 0.42

Accepts common variants: 'time'/'date'/'timestamp', 'kwh'/'usage'/'value'.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import List, Tuple

import pandas as pd

TIMESTAMP_ALIASES = {"timestamp", "time", "date", "datetime"}
KWH_ALIASES = {"kwh", "usage", "value", "consumption", "units"}


class CSVFormatError(ValueError):
    pass


def parse_meter_csv(file_bytes: bytes) -> List[Tuple[datetime, float]]:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise CSVFormatError(f"Could not read CSV: {e}")

    cols_lower = {c.lower().strip(): c for c in df.columns}

    ts_col = next((cols_lower[a] for a in TIMESTAMP_ALIASES if a in cols_lower), None)
    kwh_col = next((cols_lower[a] for a in KWH_ALIASES if a in cols_lower), None)

    if ts_col is None or kwh_col is None:
        raise CSVFormatError(
            "CSV must have a timestamp-like column "
            f"({sorted(TIMESTAMP_ALIASES)}) and a usage-like column "
            f"({sorted(KWH_ALIASES)}). Found columns: {list(df.columns)}"
        )

    df = df[[ts_col, kwh_col]].dropna()
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    df[kwh_col] = pd.to_numeric(df[kwh_col], errors="coerce")
    df = df.dropna()

    if df.empty:
        raise CSVFormatError("No valid rows found after parsing timestamps/values.")

    return list(zip(df[ts_col].tolist(), df[kwh_col].tolist()))
