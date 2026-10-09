from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Dataset, Reading
from backend.schemas import DatasetOut
from backend.services.ingest_service import parse_meter_csv, CSVFormatError
from backend.services.pipeline_service import run_pipeline

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.uploaded_at.desc()).all()


@router.post("", response_model=DatasetOut)
def upload_dataset(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    content = file.file.read()
    try:
        rows = parse_meter_csv(content)
    except CSVFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))

    dataset = Dataset(name=file.filename, source="upload")
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    db.bulk_save_objects([
        Reading(dataset_id=dataset.id, timestamp=ts, kwh=kwh) for ts, kwh in rows
    ])
    db.commit()

    run_pipeline(db, dataset.id)
    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).get(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)
    db.commit()
    return {"deleted": dataset_id}
