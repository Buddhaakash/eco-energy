"""
Generates 30 days of hourly meter readings with realistic daily/weekly
patterns PLUS deliberately injected "leaks" so the demo has clear findings:

  1. An AC/appliance left on overnight for 5 nights (2am-5am spike)
  2. A fridge/compressor fault causing a recurring afternoon spike
  3. A gradually rising standby ("vampire") load over the month

Run:  python -m data.generate_demo_data
Output: data/sample_meter.csv  (timestamp, kwh)
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

DAYS = 30
START = datetime(2026, 8, 1, 0, 0, 0)


def base_load(hour: int, weekday: int) -> float:
    """Typical household hourly kWh by time of day, higher on weekends."""
    # Morning (6-9) and evening (18-23) peaks; low overnight.
    if 0 <= hour < 5:
        val = 0.15
    elif 5 <= hour < 9:
        val = 0.55
    elif 9 <= hour < 17:
        val = 0.35
    elif 17 <= hour < 23:
        val = 0.75
    else:
        val = 0.25

    if weekday >= 5:  # weekend: more daytime usage
        val *= 1.2
    return val


def generate() -> list[tuple[datetime, float]]:
    rows = []
    standby_creep = 0.0

    # pick 5 random nights in the last 2 weeks for the "left AC on" leak
    leak_nights = sorted(random.sample(range(DAYS - 14, DAYS), 5))
    # pick a recurring afternoon slot (e.g. faulty fridge compressor) every 3 days
    fridge_days = [d for d in range(DAYS) if d % 3 == 0]

    for day in range(DAYS):
        date = START + timedelta(days=day)
        weekday = date.weekday()
        standby_creep += 0.01  # slow rise in baseline standby draw over the month

        for hour in range(24):
            ts = date + timedelta(hours=hour)
            val = base_load(hour, weekday) + standby_creep
            val += random.uniform(-0.05, 0.05)  # small noise

            # Leak 1: overnight AC left running (2am-5am, +1.8 kWh/hr)
            if day in leak_nights and 2 <= hour < 5:
                val += 1.8

            # Leak 2: recurring afternoon compressor spike (2pm-3pm, +1.1 kWh/hr)
            if day in fridge_days and hour == 14:
                val += 1.1

            rows.append((ts, round(max(val, 0.02), 3)))

    return rows


def save_csv(rows: list[tuple[datetime, float]], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "kwh"])
        for ts, kwh in rows:
            writer.writerow([ts.isoformat(), kwh])


if __name__ == "__main__":
    rows = generate()
    save_csv(rows, "data/sample_meter.csv")
    total = sum(k for _, k in rows)
    print(f"Wrote {len(rows)} readings to data/sample_meter.csv")
    print(f"Total kWh over {DAYS} days: {total:.1f}")
