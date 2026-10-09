"""
Extracts billing period, units, and amount from an uploaded bill file
(PDF or photo/image). The AI is only ever used to READ and STRUCTURE what's
already printed on the document — this never estimates or invents a number
that isn't legible, by instruction in the prompt itself.

Two paths:
  - PDF: extract text with pypdf, then ask a text-only LLM call to parse it.
  - Image (jpg/png/etc): send the image directly to a multimodal LLM call.

Returns an ExtractionResult. If the AI is unavailable or extraction fails,
`ok` is False and the caller should fall back to the manual entry form —
this feature never silently invents numbers.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.services.llm_client import ask, ask_with_image

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bill_extract_prompt.txt"
_TEMPLATE = _PROMPT_PATH.read_text()

IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".webp": "image/webp",
}


@dataclass
class ExtractionResult:
    ok: bool
    period_start: Optional[str] = None   # "YYYY-MM-DD" or None
    period_end: Optional[str] = None
    billed_units: Optional[float] = None
    billed_amount: Optional[float] = None
    confidence: Optional[str] = None
    message: str = ""


def _parse_json_response(raw: str) -> Optional[dict]:
    if not raw:
        return None
    # Strip accidental markdown fences, just in case the model adds them.
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None


def _result_from_json(data: dict) -> ExtractionResult:
    try:
        return ExtractionResult(
            ok=True,
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
            billed_units=float(data["billed_units"]) if data.get("billed_units") is not None else None,
            billed_amount=float(data["billed_amount"]) if data.get("billed_amount") is not None else None,
            confidence=data.get("confidence", "low"),
            message="Extracted — please review before checking.",
        )
    except (ValueError, TypeError):
        return ExtractionResult(ok=False, message="Couldn't parse the extracted values. Please enter them manually.")


def extract_from_pdf_text(pdf_bytes: bytes) -> ExtractionResult:
    """
    Text PDFs: read the text with pypdf, then ask the AI to structure it.
    Scanned PDFs (no text layer): send the PDF itself to the AI, which can
    read the page images directly.
    """
    text = ""
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        text = ""  # fall through to the scanned-PDF path below

    if text.strip():
        prompt = _TEMPLATE.replace("{bill_content}", text[:6000])  # cap length sent to the model
        raw = ask(prompt, json_mode=True)
        data = _parse_json_response(raw)
    else:
        prompt = _TEMPLATE.replace("{bill_content}", "(see attached PDF of the bill)")
        raw = ask_with_image(prompt, pdf_bytes, "application/pdf")
        data = _parse_json_response(raw) if raw else None

    if data is None:
        return ExtractionResult(ok=False, message="AI extraction unavailable or failed. Please enter the details manually.")
    return _result_from_json(data)


def extract_from_image(image_bytes: bytes, filename: str) -> ExtractionResult:
    suffix = Path(filename).suffix.lower()
    mime_type = IMAGE_MIME_TYPES.get(suffix)
    if mime_type is None:
        return ExtractionResult(ok=False, message=f"Unsupported image type: {suffix or 'unknown'}")

    prompt = _TEMPLATE.replace("{bill_content}", "(see attached image of the bill)")
    raw = ask_with_image(prompt, image_bytes, mime_type)
    data = _parse_json_response(raw) if raw else None
    if data is None:
        return ExtractionResult(ok=False, message="AI extraction unavailable or failed. Please enter the details manually.")
    return _result_from_json(data)


def extract_bill_fields(file_bytes: bytes, filename: str) -> ExtractionResult:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_from_pdf_text(file_bytes)
    if suffix in IMAGE_MIME_TYPES:
        return extract_from_image(file_bytes, filename)
    return ExtractionResult(
        ok=False,
        message=f"Unsupported file type '{suffix}'. Upload a PDF or an image (jpg/png).",
    )
