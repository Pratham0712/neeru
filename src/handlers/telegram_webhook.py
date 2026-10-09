"""Telegram bot webhook: POST /telegram (API Gateway).

Conversation:
  /start or /lang        -> pick English or Kannada
  photo                  -> "now share your location" (photo kept for 15 minutes)
  location after a photo -> verify the photo with the agent, reply with the verdict
  location on its own    -> flood risk at the 3 nearest hotspots, with "Alert me" buttons
  /stop                  -> unsubscribe from every alert

Telegram retries a webhook that times out, so each update_id is processed once only.
"""

import base64
import hmac
import json
import logging
from datetime import datetime, timedelta

from neeru import config, engine, geo, i18n, images, store, telegram

log = logging.getLogger()
log.setLevel(logging.INFO)

PHOTO_TTL = timedelta(minutes=15)
NEARBY_RADIUS_KM = 5.0
OK = {"statusCode": 200, "body": "ok"}


def handler(event, _context):
    supplied = (event.get("headers") or {}).get("x-telegram-bot-api-secret-token", "")
    if not config.TELEGRAM_SECRET or not hmac.compare_digest(supplied, config.TELEGRAM_SECRET):
        return {"statusCode": 403, "body": "forbidden"}

    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode()
    update = json.loads(body)

    if not store.claim_update(update["update_id"]):
        return OK  # a retry of something we already handled

    try:
        if "callback_query" in update:
            on_button(update["callback_query"])
        elif "message" in update:
            on_message(update["message"])
    except Exception:
        log.exception("update failed")
        chat_id = (update.get("message") or {}).get("chat", {}).get("id")
        if chat_id:
            telegram.send_message(chat_id, i18n.t("error", store.get_session(chat_id).get("lang", "en")))
    return OK


# ---------- buttons ----------

def on_button(query: dict) -> None:
    chat_id = query["message"]["chat"]["id"]
    session = store.get_session(chat_id)
    data = query.get("data", "")

    if data.startswith("lang:"):
        session["lang"] = "kn" if data == "lang:kn" else "en"
        store.put_session(session)
        telegram.answer_callback(query["id"])
        telegram.send_message(chat_id, i18n.t("welcome", session["lang"]),
                              telegram.location_keyboard(i18n.t("share_location_button", session["lang"])))
    elif data.startswith("sub:"):
        hotspot = store.get_hotspot(data[4:])
        if hotspot:
            lang = session.get("lang", "en")
            store.subscribe(hotspot["id"], chat_id, lang)
            name = i18n.place_name(hotspot, lang)
            telegram.answer_callback(query["id"], "🔔")
            telegram.send_message(chat_id, i18n.t("subscribed", lang, name=name))


# ---------- messages ----------

def on_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    session = store.get_session(chat_id)
    lang = session.get("lang", "en")
    text = (message.get("text") or "").strip()

    if text.startswith("/start") or text.startswith("/lang"):
        telegram.send_message(chat_id, i18n.t("choose_lang", lang),
                              telegram.inline_keyboard([[("English", "lang:en"), ("ಕನ್ನಡ", "lang:kn")]]))
    elif text.startswith("/stop"):
        count = store.unsubscribe_all(chat_id)
        telegram.send_message(chat_id, i18n.t("stopped", lang, n=count))
    elif photo_file_id(message):
        session["pending_photo"] = photo_file_id(message)
        session["pending_at"] = store.now_utc().isoformat()
        store.put_session(session)
        telegram.send_message(chat_id, i18n.t("ask_location", lang),
                              telegram.location_keyboard(i18n.t("share_location_button", lang)))
    elif "location" in message:
        lat, lon = message["location"]["latitude"], message["location"]["longitude"]
        if has_fresh_photo(session):
            handle_report(chat_id, session, lat, lon)
        else:
            handle_nearby(chat_id, lang, lat, lon)
    else:
        telegram.send_message(chat_id, i18n.t("welcome", lang),
                              telegram.location_keyboard(i18n.t("share_location_button", lang)))


def photo_file_id(message: dict) -> str | None:
    """Largest size of a photo, or an image sent 'as a file'."""
    if message.get("photo"):
        return message["photo"][-1]["file_id"]
    document = message.get("document") or {}
    if document.get("mime_type", "").startswith("image/"):
        return document["file_id"]
    return None


def has_fresh_photo(session: dict) -> bool:
    if not session.get("pending_photo"):
        return False
    return datetime.fromisoformat(session["pending_at"]) > store.now_utc() - PHOTO_TTL


def handle_report(chat_id: int, session: dict, lat: float, lon: float) -> None:
    lang = session.get("lang", "en")
    telegram.send_message(chat_id, i18n.t("checking", lang), {"remove_keyboard": True})

    image = telegram.download_file(session.pop("pending_photo"))
    session.pop("pending_at", None)
    store.put_session(session)

    image_format = images.detect_format(image)
    if image_format is None or len(image) > images.MAX_IMAGE_BYTES:
        telegram.send_message(chat_id, i18n.t("verdict_invalid", lang))
        return

    result = engine.process_report(image, image_format, lat, lon, lang=lang, source="telegram")
    telegram.send_message(chat_id, *verdict_reply(result, lang))


def verdict_reply(result: dict, lang: str) -> tuple[str, dict | None]:
    """The bot's answer to a report, and an optional 'Alert me' button."""
    if result["status"] == "outside_city":
        return i18n.t("outside_city", lang), None

    verdict = result["verdict"]
    hotspot = result.get("hotspot")
    place = i18n.place_name(hotspot, lang) if hotspot else i18n.t("your_location", lang)

    if not verdict["is_valid_photo"]:
        return i18n.t("verdict_invalid", lang), None
    if not verdict["verified"]:
        text = i18n.t("verdict_unverified", lang)
    elif verdict["is_waterlogging"]:
        text = i18n.t("verdict_flooded", lang, depth=i18n.depth(verdict["depth"], lang), place=place)
        if result.get("new_spot"):
            text += "\n" + i18n.t("new_spot", lang)
    else:
        text = i18n.t("verdict_dry", lang, place=place)

    if verdict.get("rider_advice"):
        text += "\n\n" + verdict["rider_advice"]

    button = None
    if hotspot:
        button = telegram.inline_keyboard([[(i18n.t("alert_me", lang, name=place), f"sub:{hotspot['id']}")]])
    return text, button


def handle_nearby(chat_id: int, lang: str, lat: float, lon: float) -> None:
    nearby = [(h, d) for h, d in geo.nearest(lat, lon, store.list_hotspots(), 3) if d <= NEARBY_RADIUS_KM]
    if not nearby:
        telegram.send_message(chat_id, i18n.t("no_spots", lang), {"remove_keyboard": True})
        return

    lines = [i18n.t("nearby_header", lang)]
    buttons = []
    replay = False
    for hotspot, distance in nearby:
        level = hotspot.get("risk", {}).get("level", "green")
        name = i18n.place_name(hotspot, lang)
        lines.append(f"{i18n.level(level, lang)} · {name} · {distance:.1f} km")
        buttons.append([(i18n.t("alert_me", lang, name=name), f"sub:{hotspot['id']}")])
        replay = replay or hotspot.get("rain", {}).get("source") == "storm-replay"
    if replay:
        lines.append(i18n.t("replay_note", lang))
    telegram.send_message(chat_id, "\n".join(lines), telegram.inline_keyboard(buttons))
