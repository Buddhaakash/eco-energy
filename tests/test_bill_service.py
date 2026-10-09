"""
Run with: pytest tests/test_bill_service.py -v
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from backend.services.bill_service import check_bill


def _readings(days=7, kwh_per_day=10.0):
    start = datetime(2026, 1, 1)
    return [
        (start + timedelta(days=d, hours=h), kwh_per_day / 24)
        for d in range(days) for h in range(24)
    ]


def test_matching_bill_is_not_flagged():
    readings = _readings(days=7, kwh_per_day=10.0)
    period_start, period_end = readings[0][0], readings[-1][0]
    total_kwh = sum(k for _, k in readings)

    result = check_bill(
        readings, period_start, period_end,
        billed_units=total_kwh, billed_amount=total_kwh * 8.0,
        tariff_per_kwh=8.0,
    )
    assert result.severity == "ok"
    assert result.flagged is False


def test_inflated_bill_is_flagged_major():
    readings = _readings(days=7, kwh_per_day=10.0)
    period_start, period_end = readings[0][0], readings[-1][0]
    total_kwh = sum(k for _, k in readings)

    result = check_bill(
        readings, period_start, period_end,
        billed_units=total_kwh * 1.5, billed_amount=total_kwh * 8.0 * 1.5,
        tariff_per_kwh=8.0,
    )
    assert result.severity == "major"
    assert result.flagged is True
    assert result.cost_gap > 0


def test_slightly_higher_bill_is_minor():
    readings = _readings(days=7, kwh_per_day=10.0)
    period_start, period_end = readings[0][0], readings[-1][0]
    total_kwh = sum(k for _, k in readings)
    expected_cost = total_kwh * 8.0

    # ~15% over -> should land in "minor" band (tolerance=8%, minor up to 24%)
    result = check_bill(
        readings, period_start, period_end,
        billed_units=total_kwh, billed_amount=expected_cost * 1.15,
        tariff_per_kwh=8.0,
    )
    assert result.severity == "minor"


def test_readings_outside_period_are_excluded():
    readings = _readings(days=10, kwh_per_day=10.0)
    # Only check the first 3 days
    period_start = readings[0][0]
    period_end = readings[0][0] + timedelta(days=3)
    in_period_kwh = sum(k for t, k in readings if period_start <= t <= period_end)

    result = check_bill(
        readings, period_start, period_end,
        billed_units=in_period_kwh, billed_amount=in_period_kwh * 8.0,
        tariff_per_kwh=8.0,
    )
    assert result.metered_kwh == round(in_period_kwh, 3)
    assert result.severity == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
