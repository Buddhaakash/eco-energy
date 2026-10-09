from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Recommendation
from backend.schemas import RecommendationOut, RecommendationStatusUpdate

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

VALID_STATUSES = {"open", "done", "snoozed"}


@router.get("", response_model=List[RecommendationOut])
def list_recommendations(dataset_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Recommendation)
        .filter(Recommendation.dataset_id == dataset_id)
        .order_by(Recommendation.priority)
        .all()
    )


@router.patch("/{rec_id}", response_model=RecommendationOut)
def update_recommendation_status(
    rec_id: int, update: RecommendationStatusUpdate, db: Session = Depends(get_db)
):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {VALID_STATUSES}")

    rec = db.query(Recommendation).get(rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.status = update.status
    db.commit()
    db.refresh(rec)
    return rec
