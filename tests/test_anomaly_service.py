"""
Run with: pytest tests/test_anomaly_service.py -v
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.anomaly_service import detect_anomalies


def _flat_readings(days=5, base=0.3):
    """Perfectly flat usage — should produce zero anomalies."""
    start = datetime(2026, 1, 1)
    rows = []
    for d in range(days):
        for h in range(24):
            rows.append({"timestamp": start + timedelta(days=d, hours=h), "kwh": base})
    return pd.DataFrame(rows)


def _readings_with_night_spike():
    """5 flat days, then one night with a clear 2am-4am spike."""
    start = datetime(2026, 1, 1)
    rows = []
    for d in range(6):
        for h in range(24):
            kwh = 0.2
            if d == 5 and 2 <= h <= 4:
                kwh = 3.0  # obvious leak
            rows.append({"timestamp": start + timedelta(days=d, hours=h), "kwh": kwh})
    return pd.DataFrame(rows)


def test_empty_readings_returns_no_anomalies():
    df = pd.DataFrame(columns=["timestamp", "kwh"])
    assert detect_anomalies(df) == []


def test_flat_usage_produces_no_anomalies():
    df = _flat_readings()
    events = detect_anomalies(df, sensitivity="medium")
    assert events == []


def test_detects_injected_night_spike():
    df = _readings_with_night_spike()
    events = detect_anomalies(df, sensitivity="medium")
    assert len(events) >= 1
    assert any(e.kind == "night_load" for e in events)
    night_events = [e for e in events if e.kind == "night_load"]
    assert night_events[0].severity == "high"


def test_high_sensitivity_flags_more_than_low():
    df = _readings_with_night_spike()
    low = detect_anomalies(df, sensitivity="low")
    high = detect_anomalies(df, sensitivity="high")
    assert len(high) >= len(low)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
