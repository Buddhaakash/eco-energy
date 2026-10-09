"""
Turns detected anomalies + settings into ₹ figures and a savings plan.
Still no AI here — this is deterministic arithmetic so the numbers
shown on the dashboard are always reproducible and defensible.
"""
from __future__ import annotations

from typing import List

from backend.services.anomaly_service import AnomalyEvent

DAYS_PER_MONTH = 30


def cost_of(kwh: float, tariff_per_kwh: float) -> float:
    return round(kwh * tariff_per_kwh, 2)


def compute_kpis(
    total_kwh: float,
    days_covered: int,
    anomalies: List[AnomalyEvent],
    tariff_per_kwh: float,
) -> dict:
    total_cost = cost_of(total_kwh, tariff_per_kwh)
    daily_avg_kwh = total_kwh / max(days_covered, 1)
    projected_monthly_cost = cost_of(daily_avg_kwh * DAYS_PER_MONTH, tariff_per_kwh)

    leak_kwh = sum(a.extra_kwh for a in anomalies)
    potential_savings = cost_of(leak_kwh, tariff_per_kwh)

    return {
        "total_kwh": round(total_kwh, 2),
        "total_cost": total_cost,
        "projected_monthly_cost": projected_monthly_cost,
        "leak_count": len(anomalies),
        "potential_savings": potential_savings,
    }


def build_recommendations(
    anomalies: List[AnomalyEvent], tariff_per_kwh: float
) -> list[dict]:
    """
    Groups anomalies by kind and produces one ranked, actionable
    recommendation per kind — this is what AI advisor_service.py
    will later turn into friendlier wording, but the underlying
    action + numbers are computed here so they can't be hallucinated.
    """
    by_kind: dict[str, list[AnomalyEvent]] = {}
    for a in anomalies:
        by_kind.setdefault(a.kind, []).append(a)

    recs = []

    if "night_load" in by_kind:
        events = by_kind["night_load"]
        extra_kwh = sum(e.extra_kwh for e in events)
        recs.append({
            "title": "Cut overnight standby load",
            "detail": (
                f"Unusually high usage detected between 12am-5am on "
                f"{len(events)} night(s), likely a device (AC, heater, "
                f"pump) left running. Check what's on overnight and use "
                f"a timer or smart plug to shut it off automatically."
            ),
            "est_kwh_saved": round(extra_kwh, 2),
            "est_cost_saved": cost_of(extra_kwh, tariff_per_kwh),
            "priority": 1,
        })

    if "spike" in by_kind:
        events = by_kind["spike"]
        extra_kwh = sum(e.extra_kwh for e in events)
        recs.append({
            "title": "Investigate recurring daytime spikes",
            "detail": (
                f"{len(events)} unusual spike(s) found during the day. "
                f"This pattern often points to a faulty appliance "
                f"(fridge compressor, water heater) drawing more power "
                f"than normal. Consider having it serviced."
            ),
            "est_kwh_saved": round(extra_kwh, 2),
            "est_cost_saved": cost_of(extra_kwh, tariff_per_kwh),
            "priority": 2,
        })

    # generic always-included tip so the plan never looks empty
    recs.append({
        "title": "Shift heavy appliance use to off-peak hours",
        "detail": (
            "Running washing machines, water heaters and pumps outside "
            "peak evening hours (6pm-11pm) reduces strain and can lower "
            "time-of-use tariffs where applicable."
        ),
        "est_kwh_saved": 0.0,
        "est_cost_saved": 0.0,
        "priority": 3,
    })

    recs.sort(key=lambda r: r["priority"])
    return recs
