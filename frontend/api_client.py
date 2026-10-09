"""
Thin wrapper around the FastAPI backend. Every Streamlit component calls
functions from here instead of using `requests` directly, so the base URL
and error handling live in one place.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    "API_URL",
    "https://eco-energy-m65z.onrender.com"
).rstrip("/")

def _get(path: str, params: dict | None = None) -> dict | list:
    r = httpx.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _put(path: str, json: dict) -> dict:
    r = httpx.put(f"{API_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json()


def _patch(path: str, json: dict) -> dict:
    r = httpx.patch(f"{API_URL}{path}", json=json, timeout=30)
    r.raise_for_status()
    return r.json()


def _post_json(path: str, json: dict) -> dict:
    r = httpx.post(f"{API_URL}{path}", json=json, timeout=60)
    r.raise_for_status()
    return r.json()


# ---------- Datasets ----------

def list_datasets() -> list[dict]:
    return _get("/api/datasets")


def upload_dataset(filename: str, file_bytes: bytes) -> dict:
    r = httpx.post(
        f"{API_URL}/api/datasets",
        files={"file": (filename, file_bytes, "text/csv")},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()


def delete_dataset(dataset_id: int) -> None:
    r = httpx.delete(f"{API_URL}/api/datasets/{dataset_id}", timeout=30)
    r.raise_for_status()


# ---------- Analysis ----------

def get_analysis(dataset_id: int) -> dict:
    return _get(f"/api/analysis/{dataset_id}")


# ---------- Anomalies ----------

def list_anomalies(dataset_id: int) -> list[dict]:
    return _get("/api/anomalies", params={"dataset_id": dataset_id})


def update_anomaly_status(anomaly_id: int, status: str) -> dict:
    return _patch(f"/api/anomalies/{anomaly_id}", {"status": status})


# ---------- Recommendations ----------

def list_recommendations(dataset_id: int) -> list[dict]:
    return _get("/api/recommendations", params={"dataset_id": dataset_id})


def update_recommendation_status(rec_id: int, status: str) -> dict:
    return _patch(f"/api/recommendations/{rec_id}", {"status": status})


# ---------- Settings ----------

def get_settings() -> dict:
    return _get("/api/settings")


def update_settings(**kwargs) -> dict:
    return _put("/api/settings", {k: v for k, v in kwargs.items() if v is not None})


# ---------- Chat ----------

def ask_ai(dataset_id: int, question: str) -> str:
    result = _post_json("/api/chat", {"dataset_id": dataset_id, "question": question})
    return result["answer"]


# ---------- Report ----------

def report_url(dataset_id: int, fmt: str = "csv") -> str:
    return f"{API_URL}/api/report/{dataset_id}.{fmt}"


# ---------- Bill Check ----------

def create_bill_check(
    dataset_id: int, period_start: str, period_end: str,
    billed_units: float, billed_amount: float,
) -> dict:
    return _post_json("/api/bill-check", {
        "dataset_id": dataset_id,
        "period_start": period_start,
        "period_end": period_end,
        "billed_units": billed_units,
        "billed_amount": billed_amount,
    })


def list_bill_checks(dataset_id: int) -> list[dict]:
    return _get("/api/bill-check", params={"dataset_id": dataset_id})


def extract_bill(filename: str, file_bytes: bytes) -> dict:
    """Uploads a bill PDF/image and gets back AI-extracted fields to review."""
    r = httpx.post(
        f"{API_URL}/api/bill-check/extract",
        files={"file": (filename, file_bytes)},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()


def safe_call(fn, *args, error_prefix: str = "Something went wrong", **kwargs):
    """Wraps an api_client call and shows a friendly Streamlit error instead
    of crashing the whole dashboard on a network hiccup."""
    try:
        return fn(*args, **kwargs)
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except ValueError:
            detail = f"server error (status {e.response.status_code}) - check the backend terminal for details"
        st.error(f"{error_prefix}: {detail}")
    except httpx.TimeoutException:
        st.error(
            f"{error_prefix}: the backend is still working on it (the AI can take a minute). "
            "Wait a minute, then press F5. If it keeps happening, restart the backend."
        )
    except httpx.RequestError:
        st.error(f"{error_prefix}: could not reach the backend at {API_URL}. Is it running?")
    return None
