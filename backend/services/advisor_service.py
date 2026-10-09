"""
Fills the advisor prompt template with ALREADY-COMPUTED numbers (from
anomaly_service / savings_service) and asks the AI only to explain them
in plain language. The AI never computes or invents the kWh/₹ figures.
"""
from __future__ import annotations

from pathlib import Path

from backend.services.llm_client import ask

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "advisor_prompt.txt"
_TEMPLATE = _PROMPT_PATH.read_text()


def explain_anomaly(
    kind: str, start, end, extra_kwh: float, est_cost: float, severity: str
) -> str:
    prompt = _TEMPLATE.format(
        kind=kind.replace("_", " "),
        start=start,
        end=end,
        extra_kwh=round(extra_kwh, 2),
        est_cost=round(est_cost, 2),
        severity=severity,
    )
    return ask(prompt)
