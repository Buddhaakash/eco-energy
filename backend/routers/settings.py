from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import SettingsOut, SettingsUpdate
from backend.services.pipeline_service import get_or_create_settings, run_pipeline
from backend.models import Dataset

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    return get_or_create_settings(db)


@router.put("", response_model=SettingsOut)
def update_settings(update: SettingsUpdate, db: Session = Depends(get_db)):
    settings_row = get_or_create_settings(db)

    if update.tariff_per_kwh is not None:
        settings_row.tariff_per_kwh = update.tariff_per_kwh
    if update.monthly_budget is not None:
        settings_row.monthly_budget = update.monthly_budget
    if update.sensitivity is not None:
        settings_row.sensitivity = update.sensitivity

    db.commit()
    db.refresh(settings_row)

    # Settings changes (tariff/sensitivity) affect detection + cost figures,
    # so re-run the pipeline for every existing dataset.
    for dataset in db.query(Dataset).all():
        run_pipeline(db, dataset.id)

    return settings_row
