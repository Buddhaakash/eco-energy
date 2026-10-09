from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.report_service import build_csv_report, build_pdf_report

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/{dataset_id}.csv")
def report_csv(dataset_id: int, db: Session = Depends(get_db)):
    data = build_csv_report(db, dataset_id)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{dataset_id}.csv"},
    )


@router.get("/{dataset_id}.pdf")
def report_pdf(dataset_id: int, db: Session = Depends(get_db)):
    data = build_pdf_report(db, dataset_id)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{dataset_id}.pdf"},
    )
