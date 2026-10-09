"""
THE ONLY FILE THAT TALKS TO AN EXTERNAL AI API.

Every other service (advisor_service, chat_service, bill_extraction_service)
calls `ask(...)` / `ask_with_image(...)` from here. To switch from Gemini to
Claude or OpenAI, this is the only file you need to edit.

In .env, both settings can hold ONE value or SEVERAL separated by commas:
    AI_API_KEY=key_one,key_two
    AI_MODEL=gemini-3.8-flash,gemini-flash-latest
Attempts are made in this order: every key for the first model, then every
key for the second model, and so on. The first answer wins. If everything
fails, a safe fallback is returned and the app keeps working.

Note: these must all be Google Gemini keys/models.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from backend.config import settings

_FALLBACK_MESSAGE = (
    "AI explanation unavailable right now — showing the calculated figures only."
)

_TIMEOUT_SECONDS = 40   # give up on one attempt after this long and try the next


def api_keys() -> List[str]:
    """The API keys listed in AI_API_KEY, in the order they will be tried."""
    return [k.strip() for k in settings.AI_API_KEY.split(",") if k.strip()]


def model_names() -> List[str]:
    """The model names listed in AI_MODEL, in the order they will be tried."""
    return [m.strip() for m in settings.AI_MODEL.split(",") if m.strip()]


def _attempts() -> List[Tuple[str, str]]:
    """(key, model) pairs: all keys for model 1, then all keys for model 2, ..."""
    keys = api_keys()
    return [(key, name) for name in model_names() for key in keys]


def _call(key: str, model_name: str, contents, generation_config: dict):
    import google.generativeai as genai

    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    return model.generate_content(
        contents,
        generation_config=generation_config,
        request_options={"timeout": _TIMEOUT_SECONDS},
    )


def ask(prompt: str, *, json_mode: bool = False) -> str:
    """
    Sends `prompt` to the AI and returns the text response, trying each
    key/model combination in order. Never raises: returns a fallback
    string if every attempt fails.
    """
    generation_config = {"response_mime_type": "application/json"} if json_mode else {}
    for key, name in _attempts():
        try:
            text = (_call(key, name, prompt, generation_config).text or "").strip()
            if text:
                return text
        except Exception:
            continue  # this key/model failed (retired / busy / quota), try the next
    return _FALLBACK_MESSAGE


def ask_with_image(prompt: str, image_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Sends a prompt + an image or PDF (e.g. a bill) to the AI and asks for
    strict JSON back. Returns None (not a fallback string) if every attempt
    fails, so callers can tell "AI unavailable" apart from a normal answer.
    """
    contents = [prompt, {"mime_type": mime_type, "data": image_bytes}]
    for key, name in _attempts():
        try:
            text = (
                _call(key, name, contents, {"response_mime_type": "application/json"}).text or ""
            ).strip()
            if text:
                return text
        except Exception:
            continue
    return None
