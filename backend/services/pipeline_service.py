"""
Runs the full analysis pipeline for one dataset:
  1. Load readings from the DB into a DataFrame
  2. Detect anomalies (anomaly_service)
  3. Get AI explanations for each anomaly (advisor_service)
  4. Compute recommendations (savings_service)
  5. Replace any existing Anomaly/Recommendation rows for this dataset

Called whenever a dataset is uploaded/seeded, or when the user changes
tariff/sensitivity settings and needs a re-analysis.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from backend.models import Reading, Anomaly, Recommendation, AppSettings
from backend.services.anomaly_service import detect_anomalies
from backend.services.savings_service import build_recommendations
from backend.services.advisor_service import explain_anomaly


def get_or_create_settings(db: Session) -> AppSettings:
    settings_row = db.query(AppSettings).first()
    if settings_row is None:
        settings_row = AppSettings(id=1)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def run_pipeline(db: Session, dataset_id: int) -> None:
    settings_row = get_or_create_settings(db)

    readings = db.query(Reading).filter(Reading.dataset_id == dataset_id).all()
    if not readings:
        return

    df = pd.DataFrame(
        [{"timestamp": r.timestamp, "kwh": r.kwh} for r in readings]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    events = detect_anomalies(df, sensitivity=settings_row.sensitivity)

    # clear previous results for this dataset so re-runs don't duplicate
    db.query(Anomaly).filter(Anomaly.dataset_id == dataset_id).delete()
    db.query(Recommendation).filter(Recommendation.dataset_id == dataset_id).delete()
    db.commit()

    for e in events:
        explanation = explain_anomaly(
            e.kind, e.start, e.end, e.extra_kwh,
            round(e.extra_kwh * settings_row.tariff_per_kwh, 2), e.severity,
        )
        db.add(Anomaly(
            dataset_id=dataset_id,
            start=e.start,
            end=e.end,
            kind=e.kind,
            extra_kwh=e.extra_kwh,
            est_cost=round(e.extra_kwh * settings_row.tariff_per_kwh, 2),
            severity=e.severity,
            explanation=explanation,
            status="new",
        ))

    recs = build_recommendations(events, settings_row.tariff_per_kwh)
    for r in recs:
        db.add(Recommendation(dataset_id=dataset_id, status="open", **r))

    db.commit()
