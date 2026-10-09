"""
Downloads the UCI "Individual Household Electric Power Consumption" dataset
and converts it into the timestamp/kwh hourly CSV format EcoEnergy expects.

Run (needs internet, on your own machine, not in this sandbox):
    pip install ucimlrepo pandas
    python data/fetch_real_dataset.py

Output: data/real_household_meter.csv
    -> upload this file directly on the Data tab of the dashboard.

Note: this is minute-level Global_active_power in KILOWATTS. We convert to
hourly kWh by: (kW averaged per minute) -> sum of (kW * 1/60 hour) per hour.
"""
from __future__ import annotations

import pandas as pd


def fetch_and_convert(months_limit: int | None = 3) -> pd.DataFrame:
    """
    months_limit: keep only the first N months of data (the full dataset is
    ~4 years / 2 million rows, which is overkill for a hackathon dashboard
    and slow to upload/process). Set to None to keep everything.
    """
    from ucimlrepo import fetch_ucirepo

    print("Downloading dataset (this can take a minute)...")
    dataset = fetch_ucirepo(id=235)
    df = dataset.data.features.copy()

    print(f"Raw rows: {len(df):,}")

    # Build a proper datetime index from Date + Time columns
    df["timestamp"] = pd.to_datetime(
        df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )
    df = df.dropna(subset=["timestamp"])

    # Global_active_power is in kilowatts, sampled once per minute.
    # Convert to numeric (raw file has some '?' missing-value markers)
    df["Global_active_power"] = pd.to_numeric(df["Global_active_power"], errors="coerce")
    df = df.dropna(subset=["Global_active_power"])

    if months_limit:
        cutoff = df["timestamp"].min() + pd.DateOffset(months=months_limit)
        df = df[df["timestamp"] < cutoff]
        print(f"Limited to first {months_limit} month(s): {len(df):,} rows")

    df = df.set_index("timestamp")

    # kW measured once per minute -> kWh per hour = mean(kW in that hour) * 1h
    hourly = df["Global_active_power"].resample("1h").mean().to_frame("kwh")
    hourly = hourly.dropna().reset_index()

    print(f"Converted to {len(hourly):,} hourly readings")
    return hourly


if __name__ == "__main__":
    hourly = fetch_and_convert(months_limit=3)  # ~3 months is plenty for a demo
    out_path = "data/real_household_meter.csv"
    hourly.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    print(hourly.head())