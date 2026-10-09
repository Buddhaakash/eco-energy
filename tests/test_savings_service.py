"""
Run with: pytest tests/test_savings_service.py -v
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from backend.services.anomaly_service import AnomalyEvent
from backend.services.savings_service import (
    cost_of, compute_kpis, build_recommendations,
)


def test_cost_of_basic_multiplication():
    assert cost_of(10, 8.0) == 80.0
    assert cost_of(0, 8.0) == 0.0


def test_compute_kpis_no_anomalies():
    kpis = compute_kpis(total_kwh=300, days_covered=30, anomalies=[], tariff_per_kwh=8.0)
    assert kpis["total_kwh"] == 300
    assert kpis["total_cost"] == 2400.0
    assert kpis["leak_count"] == 0
    assert kpis["potential_savings"] == 0.0


def test_compute_kpis_with_anomalies():
    events = [
        AnomalyEvent(datetime(2026, 1, 1), datetime(2026, 1, 1), "night_load", 5.0, "high"),
        AnomalyEvent(datetime(2026, 1, 2), datetime(2026, 1, 2), "spike", 2.0, "medium"),
    ]
    kpis = compute_kpis(total_kwh=300, days_covered=30, anomalies=events, tariff_per_kwh=8.0)
    assert kpis["leak_count"] == 2
    assert kpis["potential_savings"] == cost_of(7.0, 8.0)


def test_build_recommendations_groups_by_kind():
    events = [
        AnomalyEvent(datetime(2026, 1, 1), datetime(2026, 1, 1), "night_load", 5.0, "high"),
        AnomalyEvent(datetime(2026, 1, 2), datetime(2026, 1, 2), "night_load", 3.0, "medium"),
        AnomalyEvent(datetime(2026, 1, 3), datetime(2026, 1, 3), "spike", 1.5, "low"),
    ]
    recs = build_recommendations(events, tariff_per_kwh=8.0)
    titles = [r["title"] for r in recs]
    assert any("overnight" in t.lower() for t in titles)
    assert any("daytime" in t.lower() for t in titles)
    # highest priority (1) should come first
    assert recs[0]["priority"] <= recs[-1]["priority"]


def test_build_recommendations_always_includes_generic_tip():
    recs = build_recommendations([], tariff_per_kwh=8.0)
    assert len(recs) >= 1
    assert any("off-peak" in r["title"].lower() for r in recs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
