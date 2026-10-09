"""
Database tables.

Dataset        -> one uploaded CSV or the demo dataset
Reading        -> one meter reading (timestamp, kWh) belonging to a Dataset
Anomaly        -> a detected leak/spike, with a user-editable status
Recommendation -> a ranked savings action, with a user-editable status
AppSettings    -> single-row table: tariff, budget goal, sensitivity
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source = Column(String, default="upload")  # "upload" | "demo"
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    readings = relationship(
        "Reading", back_populates="dataset", cascade="all, delete-orphan"
    )
    anomalies = relationship(
        "Anomaly", back_populates="dataset", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "Recommendation", back_populates="dataset", cascade="all, delete-orphan"
    )


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    kwh = Column(Float, nullable=False)

    dataset = relationship("Dataset", back_populates="readings")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    kind = Column(String, nullable=False)       # "spike" | "night_load" | "sustained"
    extra_kwh = Column(Float, nullable=False)
    est_cost = Column(Float, nullable=False)
    severity = Column(String, nullable=False)   # "low" | "medium" | "high"
    explanation = Column(Text, default="")       # filled in by the AI advisor
    status = Column(String, default="new")       # "new" | "expected" | "fixed" | "ignored"

    dataset = relationship("Dataset", back_populates="anomalies")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    title = Column(String, nullable=False)
    detail = Column(Text, default="")
    est_kwh_saved = Column(Float, default=0.0)
    est_cost_saved = Column(Float, default=0.0)
    priority = Column(Integer, default=2)         # 1=high 2=medium 3=low
    status = Column(String, default="open")        # "open" | "done" | "snoozed"

    dataset = relationship("Dataset", back_populates="recommendations")


class AppSettings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    tariff_per_kwh = Column(Float, default=8.0)     # ₹ per unit
    monthly_budget = Column(Float, default=2000.0)  # ₹
    sensitivity = Column(String, default="medium")  # "low" | "medium" | "high"


class BillCheck(Base):
    """A user-entered bill compared against their metered readings for the
    same period. Lets the user paste in what their bill says and see
    whether it lines up with what their own data says they actually used —
    flagging a mismatch as a possible unwanted charge."""
    __tablename__ = "bill_checks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    metered_kwh = Column(Float, nullable=False)
    expected_cost = Column(Float, nullable=False)
    billed_units = Column(Float, nullable=False)
    billed_amount = Column(Float, nullable=False)
    unit_gap = Column(Float, nullable=False)
    cost_gap = Column(Float, nullable=False)
    gap_pct = Column(Float, nullable=False)
    flagged = Column(Boolean, nullable=False)
    severity = Column(String, nullable=False)   # "ok" | "minor" | "major"
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset")
