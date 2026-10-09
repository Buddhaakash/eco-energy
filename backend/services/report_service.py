"""
Builds a downloadable report of a dataset's findings.
CSV export is always available; PDF uses fpdf2 for a simple one-pager.
"""
from __future__ import annotations

import io

from sqlalchemy.orm import Session

from backend.models import Anomaly, Recommendation, Dataset


def build_csv_report(db: Session, dataset_id: int) -> bytes:
    dataset = db.query(Dataset).get(dataset_id)
    anomalies = db.query(Anomaly).filter(Anomaly.dataset_id == dataset_id).all()
    recs = db.query(Recommendation).filter(Recommendation.dataset_id == dataset_id).all()

    lines = [f"EcoEnergy Report - {dataset.name if dataset else dataset_id}", ""]
    lines.append("ANOMALIES")
    lines.append("start,end,kind,extra_kwh,est_cost,severity,status")
    for a in anomalies:
        lines.append(f"{a.start},{a.end},{a.kind},{a.extra_kwh},{a.est_cost},{a.severity},{a.status}")

    lines.append("")
    lines.append("RECOMMENDATIONS")
    lines.append("title,est_kwh_saved,est_cost_saved,priority,status")
    for r in recs:
        lines.append(f"{r.title},{r.est_kwh_saved},{r.est_cost_saved},{r.priority},{r.status}")

    return "\n".join(lines).encode("utf-8")


def build_pdf_report(db: Session, dataset_id: int) -> bytes:
    from fpdf import FPDF

    dataset = db.query(Dataset).get(dataset_id)
    anomalies = db.query(Anomaly).filter(Anomaly.dataset_id == dataset_id).all()
    recs = db.query(Recommendation).filter(Recommendation.dataset_id == dataset_id).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "EcoEnergy Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Dataset: {dataset.name if dataset else dataset_id}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Detected Issues", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for a in anomalies:
        text = f"- {a.kind} on {a.start}: +{a.extra_kwh} kWh (~Rs.{a.est_cost}), {a.severity}, {a.status}"
        pdf.multi_cell(0, 6, text)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Savings Plan", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for r in recs:
        text = f"- {r.title}: saves ~{r.est_kwh_saved} kWh (~Rs.{r.est_cost_saved}) [{r.status}]"
        pdf.multi_cell(0, 6, text)

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")
