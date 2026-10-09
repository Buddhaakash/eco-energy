"""
Fills the bill-check prompt with already-computed numbers (from
bill_service.check_bill) and asks the AI to explain them in plain
language. The AI never recomputes the gap — it only narrates it.
"""
from __future__ import annotations

from pathlib import Path

from backend.services.bill_service import BillCheckResult
from backend.services.llm_client import ask

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bill_prompt.txt"
_TEMPLATE = _PROMPT_PATH.read_text()


def explain_bill_check(result: BillCheckResult) -> str:
    direction = "higher than expected" if result.cost_gap > 0 else "lower than expected"
    prompt = _TEMPLATE.format(
        period_start=result.period_start,
        period_end=result.period_end,
        metered_kwh=result.metered_kwh,
        expected_cost=result.expected_cost,
        billed_units=result.billed_units,
        billed_amount=result.billed_amount,
        cost_gap=abs(result.cost_gap),
        gap_pct_display=round(abs(result.gap_pct) * 100, 1),
        direction=direction,
        severity=result.severity,
    )
    return ask(prompt)
