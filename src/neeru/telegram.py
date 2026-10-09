"""Minimal Telegram Bot API client using only the standard library (keeps the Lambda package small)."""

import json
import logging
import urllib.request

from . import config

log = logging.getLogger(__name__)


def _call(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/{method}"
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.load(response)
    except Exception:
        log.exception("Telegram %s failed", method)
        return {"ok": False}


def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _call("sendMessage", payload)


def answer_callback(callback_id: str, text: str = "") -> dict:
    return _call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})


def download_file(file_id: str) -> bytes:
    info = _call("getFile", {"file_id": file_id})
    if not info.get("ok"):
        raise RuntimeError("getFile failed")
    url = f"https://api.telegram.org/file/bot{config.TELEGRAM_BOT_TOKEN}/{info['result']['file_path']}"
    with urllib.request.urlopen(url, timeout=15) as response:
        return response.read()


def location_keyboard(button_text: str) -> dict:
    return {
        "keyboard": [[{"text": button_text, "request_location": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }


def inline_keyboard(rows: list[list[tuple[str, str]]]) -> dict:
    """rows of (label, callback_data)."""
    return {"inline_keyboard": [[{"text": label, "callback_data": data} for label, data in row] for row in rows]}
