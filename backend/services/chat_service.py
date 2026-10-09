"""
Powers the "Ask AI" tab. Builds a compact text summary of the dataset's
anomalies and recommendations (already computed, stored in the DB) and
lets the AI answer free-text questions grounded only in those facts.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from backend.models import Anomaly, Recommendation, Reading
from backend.services.llm_client import ask

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "chat_prompt.txt"
_TEMPLATE = _PROMPT_PATH.read_text()


def _summarize_readings(db: Session, dataset_id: int) -> str:
    readings = db.query(Reading).filter(Reading.dataset_id == dataset_id).all()
    if not readings:
        return "No readings available."
    total = sum(r.kwh for r in readings)
    days = max((max(r.timestamp for r in readings) - min(r.timestamp for r in readings)).days, 1)
    return f"{len(readings)} hourly readings over {days} days, total {total:.1f} kWh."


def _summarize_anomalies(db: Session, dataset_id: int) -> str:
    anomalies = db.query(Anomaly).filter(Anomaly.dataset_id == dataset_id).all()
    if not anomalies:
        return "No anomalies detected."
    lines = [
        f"- {a.kind} on {a.start} ({a.severity} severity, +{a.extra_kwh} kWh, "
        f"~₹{a.est_cost}, status: {a.status})"
        for a in anomalies
    ]
    return "\n".join(lines)


def _summarize_recommendations(db: Session, dataset_id: int) -> str:
    recs = db.query(Recommendation).filter(Recommendation.dataset_id == dataset_id).all()
    if not recs:
        return "No recommendations yet."
    lines = [
        f"- {r.title}: saves ~{r.est_kwh_saved} kWh (~₹{r.est_cost_saved}), status: {r.status}"
        for r in recs
    ]
    return "\n".join(lines)


def answer_question(db: Session, dataset_id: int, question: str) -> str:
    prompt = _TEMPLATE.format(
        summary=_summarize_readings(db, dataset_id),
        anomalies=_summarize_anomalies(db, dataset_id),
        recommendations=_summarize_recommendations(db, dataset_id),
        question=question,
    )
    return ask(prompt)
