from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import BillCheck, Reading
from backend.schemas import BillCheckIn, BillCheckOut, BillExtractOut
from backend.services.bill_service import check_bill
from backend.services.bill_advisor_service import explain_bill_check
from backend.services.bill_extraction_service import extract_bill_fields
from backend.services.pipeline_service import get_or_create_settings

router = APIRouter(prefix="/api/bill-check", tags=["bill-check"])


@router.post("/extract", response_model=BillExtractOut)
def extract_bill(file: UploadFile = File(...)):
    """
    Reads an uploaded bill (PDF or image) and extracts period/units/amount
    using AI. Does NOT save anything — the frontend pre-fills the manual
    form with these values so the user can review/correct before submitting
    via POST /api/bill-check.
    """
    content = file.file.read()
    try:
        result = extract_bill_fields(content, file.filename or "")
    except Exception as e:  # show the real cause on the dashboard instead of a blank 500
        return BillExtractOut(
            ok=False,
            message=f"Internal error while reading the bill: {type(e).__name__}: {e}",
        )
    return BillExtractOut(
        ok=result.ok,
        period_start=result.period_start,
        period_end=result.period_end,
        billed_units=result.billed_units,
        billed_amount=result.billed_amount,
        confidence=result.confidence,
        message=result.message,
    )


@router.post("", response_model=BillCheckOut)
def create_bill_check(payload: BillCheckIn, db: Session = Depends(get_db)):
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end must be after period_start")

    readings = (
        db.query(Reading)
        .filter(Reading.dataset_id == payload.dataset_id)
        .all()
    )
    if not readings:
        raise HTTPException(
            status_code=404,
            detail="No meter readings found for this dataset — upload or load data first.",
        )

    settings_row = get_or_create_settings(db)

    result = check_bill(
        readings=[(r.timestamp, r.kwh) for r in readings],
        period_start=payload.period_start,
        period_end=payload.period_end,
        billed_units=payload.billed_units,
        billed_amount=payload.billed_amount,
        tariff_per_kwh=settings_row.tariff_per_kwh,
    )

    if result.metered_kwh == 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "Your selected dataset has no meter readings between "
                f"{payload.period_start.date()} and {payload.period_end.date()}, "
                "so the bill can't be compared. Pick a dataset that covers "
                "this billing period, or change the dates."
            ),
        )

    explanation = explain_bill_check(result)

    row = BillCheck(
        dataset_id=payload.dataset_id,
        period_start=result.period_start,
        period_end=result.period_end,
        metered_kwh=result.metered_kwh,
        expected_cost=result.expected_cost,
        billed_units=result.billed_units,
        billed_amount=result.billed_amount,
        unit_gap=result.unit_gap,
        cost_gap=result.cost_gap,
        gap_pct=result.gap_pct,
        flagged=result.flagged,
        severity=result.severity,
        explanation=explanation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=List[BillCheckOut])
def list_bill_checks(dataset_id: int, db: Session = Depends(get_db)):
    return (
        db.query(BillCheck)
        .filter(BillCheck.dataset_id == dataset_id)
        .order_by(BillCheck.created_at.desc())
        .all()
    )


@router.delete("/{bill_check_id}")
def delete_bill_check(bill_check_id: int, db: Session = Depends(get_db)):
    row = db.query(BillCheck).get(bill_check_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Bill check not found")
    db.delete(row)
    db.commit()
    return {"deleted": bill_check_id}
