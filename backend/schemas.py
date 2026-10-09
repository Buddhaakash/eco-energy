"""
Pydantic models used for request/response validation in the API.
Keeping these separate from the SQLAlchemy models (models.py) is deliberate:
schemas define what crosses the API boundary, models define what's stored.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


# ---------- Datasets ----------

class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    source: str
    uploaded_at: datetime


class ReadingPoint(BaseModel):
    timestamp: datetime
    kwh: float


# ---------- Anomalies ----------

class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dataset_id: int
    start: datetime
    end: datetime
    kind: str
    extra_kwh: float
    est_cost: float
    severity: str
    explanation: str
    status: str


class AnomalyStatusUpdate(BaseModel):
    status: str  # "expected" | "fixed" | "ignored" | "new"


# ---------- Recommendations ----------

class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dataset_id: int
    title: str
    detail: str
    est_kwh_saved: float
    est_cost_saved: float
    priority: int
    status: str


class RecommendationStatusUpdate(BaseModel):
    status: str  # "open" | "done" | "snoozed"


# ---------- Settings ----------

class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tariff_per_kwh: float
    monthly_budget: float
    sensitivity: str


class SettingsUpdate(BaseModel):
    tariff_per_kwh: Optional[float] = None
    monthly_budget: Optional[float] = None
    sensitivity: Optional[str] = None


# ---------- Analysis / KPIs ----------

class KPIs(BaseModel):
    total_kwh: float
    total_cost: float
    projected_monthly_cost: float
    leak_count: int
    potential_savings: float


class AnalysisOut(BaseModel):
    dataset_id: int
    kpis: KPIs
    timeline: List[ReadingPoint]
    anomalies: List[AnomalyOut]


# ---------- Chat ----------

class ChatRequest(BaseModel):
    dataset_id: int
    question: str


class ChatResponse(BaseModel):
    answer: str


# ---------- Bill Check ----------

class BillCheckIn(BaseModel):
    dataset_id: int
    period_start: datetime
    period_end: datetime
    billed_units: float
    billed_amount: float


class BillExtractOut(BaseModel):
    ok: bool
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    billed_units: Optional[float] = None
    billed_amount: Optional[float] = None
    confidence: Optional[str] = None
    message: str = ""


class BillCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dataset_id: int
    period_start: datetime
    period_end: datetime
    metered_kwh: float
    expected_cost: float
    billed_units: float
    billed_amount: float
    unit_gap: float
    cost_gap: float
    gap_pct: float
    flagged: bool
    severity: str
    explanation: str
    created_at: datetime
