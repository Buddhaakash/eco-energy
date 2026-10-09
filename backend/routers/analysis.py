from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Reading, Anomaly, Dataset
from backend.schemas import AnalysisOut, KPIs, ReadingPoint, AnomalyOut
from backend.services.savings_service import compute_kpis
from backend.services.anomaly_service import AnomalyEvent
from backend.services.pipeline_service import get_or_create_settings

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{dataset_id}", response_model=AnalysisOut)
def get_analysis(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).get(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    readings = (
        db.query(Reading)
        .filter(Reading.dataset_id == dataset_id)
        .order_by(Reading.timestamp)
        .all()
    )
    anomalies = db.query(Anomaly).filter(Anomaly.dataset_id == dataset_id).all()
    settings_row = get_or_create_settings(db)

    total_kwh = sum(r.kwh for r in readings)
    days_covered = max(
        (
            (readings[-1].timestamp - readings[0].timestamp).days
            if len(readings) > 1 else 1
        ),
        1,
    )

    events = [
        AnomalyEvent(a.start, a.end, a.kind, a.extra_kwh, a.severity)
        for a in anomalies
    ]
    kpis = compute_kpis(total_kwh, days_covered, events, settings_row.tariff_per_kwh)

    return AnalysisOut(
        dataset_id=dataset_id,
        kpis=KPIs(**kpis),
        timeline=[ReadingPoint(timestamp=r.timestamp, kwh=r.kwh) for r in readings],
        anomalies=[AnomalyOut.model_validate(a) for a in anomalies],
    )
