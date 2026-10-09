from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Anomaly
from backend.schemas import AnomalyOut, AnomalyStatusUpdate

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])

VALID_STATUSES = {"new", "expected", "fixed", "ignored"}


@router.get("", response_model=List[AnomalyOut])
def list_anomalies(dataset_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Anomaly)
        .filter(Anomaly.dataset_id == dataset_id)
        .order_by(Anomaly.start)
        .all()
    )


@router.patch("/{anomaly_id}", response_model=AnomalyOut)
def update_anomaly_status(
    anomaly_id: int, update: AnomalyStatusUpdate, db: Session = Depends(get_db)
):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")

    anomaly = db.query(Anomaly).get(anomaly_id)
    if anomaly is None:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.status = update.status
    db.commit()
    db.refresh(anomaly)
    return anomaly
