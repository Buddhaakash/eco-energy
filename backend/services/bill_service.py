"""
Compares what a user's electricity BILL says against what their actual
meter readings say it should cost. A gap beyond a small tolerance is
flagged as a possible "unwanted charge" (wrong reading, meter fault,
incorrect tariff slab, unexplained fixed fee, etc).

Pure arithmetic — no AI here. The AI (bill_advisor_service) only explains
the already-computed gap in plain language afterwards.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

TOLERANCE_PCT = 0.08  # up to 8% difference is treated as normal rounding/fees


@dataclass
class BillCheckResult:
    period_start: datetime
    period_end: datetime
    metered_kwh: float           # sum of actual readings in this period
    expected_cost: float         # metered_kwh * tariff
    billed_units: float          # what the bill says was used
    billed_amount: float         # what the bill charged
    unit_gap: float              # billed_units - metered_kwh
    cost_gap: float              # billed_amount - expected_cost
    gap_pct: float                # cost_gap / expected_cost (can be negative)
    flagged: bool                # True if gap_pct exceeds tolerance
    severity: str                  # "ok" | "minor" | "major"


def _severity(gap_pct: float) -> str:
    magnitude = abs(gap_pct)
    if magnitude <= TOLERANCE_PCT:
        return "ok"
    if magnitude <= TOLERANCE_PCT * 3:
        return "minor"
    return "major"


def check_bill(
    readings: List[tuple[datetime, float]],
    period_start: datetime,
    period_end: datetime,
    billed_units: float,
    billed_amount: float,
    tariff_per_kwh: float,
) -> BillCheckResult:
    """
    readings: list of (timestamp, kwh) tuples from the user's meter data.
    Only readings inside [period_start, period_end] are counted.
    """
    in_period = [kwh for ts, kwh in readings if period_start <= ts <= period_end]
    metered_kwh = round(sum(in_period), 3)
    expected_cost = round(metered_kwh * tariff_per_kwh, 2)

    unit_gap = round(billed_units - metered_kwh, 3)
    cost_gap = round(billed_amount - expected_cost, 2)
    gap_pct = round(cost_gap / expected_cost, 4) if expected_cost > 0 else 0.0

    severity = _severity(gap_pct)
    flagged = severity != "ok"

    return BillCheckResult(
        period_start=period_start,
        period_end=period_end,
        metered_kwh=metered_kwh,
        expected_cost=expected_cost,
        billed_units=billed_units,
        billed_amount=billed_amount,
        unit_gap=unit_gap,
        cost_gap=cost_gap,
        gap_pct=gap_pct,
        flagged=flagged,
        severity=severity,
    )
