"""
Run with: pytest tests/test_bill_extraction_service.py -v

Only tests the JSON-parsing logic, which is deterministic and doesn't need
a live AI call. The actual AI extraction calls (extract_from_pdf_text,
extract_from_image) need a real API key and network access to test.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from backend.services.bill_extraction_service import _parse_json_response, _result_from_json


def test_parses_clean_json():
    raw = '{"period_start": "2026-08-01", "billed_units": 100.5, "billed_amount": 800, "confidence": "high"}'
    data = _parse_json_response(raw)
    assert data is not None
    assert data["billed_units"] == 100.5


def test_parses_json_wrapped_in_markdown_fences():
    raw = '```json\n{"period_start": "2026-08-01", "billed_units": 50, "billed_amount": 400, "confidence": "medium"}\n```'
    data = _parse_json_response(raw)
    assert data is not None
    assert data["billed_units"] == 50


def test_garbage_response_returns_none():
    assert _parse_json_response("AI explanation unavailable right now") is None
    assert _parse_json_response("") is None
    assert _parse_json_response(None) is None


def test_result_from_json_handles_null_fields():
    result = _result_from_json({
        "period_start": None, "period_end": None,
        "billed_units": None, "billed_amount": None, "confidence": "low",
    })
    assert result.ok is True
    assert result.billed_units is None
    assert result.billed_amount is None


def test_result_from_json_full_values():
    result = _result_from_json({
        "period_start": "2026-08-01", "period_end": "2026-08-31",
        "billed_units": 142.5, "billed_amount": 1180.0, "confidence": "high",
    })
    assert result.ok is True
    assert result.billed_units == 142.5
    assert result.billed_amount == 1180.0
    assert result.confidence == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
