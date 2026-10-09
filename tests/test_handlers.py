"""Telegram webhook and HTTP API handlers."""

import base64
import json

from handlers import api, telegram_webhook
from neeru import engine, forecast, store, telegram
from neeru.forecast import Rain
from tests.conftest import JPEG

SECRET = {"x-telegram-bot-api-secret-token": "test-secret-1234567890"}
ADMIN = {"x-admin-token": "admin-token-1234567890"}
_update_id = iter(range(1000, 100000))


def tg(message=None, callback=None, headers=SECRET):
    update = {"update_id": next(_update_id)}
    if message:
        update["message"] = {"chat": {"id": 42}, **message}
    if callback:
        update["callback_query"] = {"id": "cb1", "message": {"chat": {"id": 42}}, **callback}
    return telegram_webhook.handler({"headers": headers, "body": json.dumps(update)}, None)


# ---------- Telegram ----------

def test_rejects_requests_without_the_secret(aws):
    assert tg({"text": "/start"}, headers={})["statusCode"] == 403


def test_duplicate_updates_are_processed_once(aws, sent):
    event = {"headers": SECRET, "body": json.dumps({"update_id": 7, "message": {"chat": {"id": 42}, "text": "/start"}})}
    telegram_webhook.handler(event, None)
    telegram_webhook.handler(event, None)
    assert len(sent) == 1


def test_language_choice_then_kannada_welcome(aws, sent):
    tg({"text": "/start"})
    assert "ಕನ್ನಡ" in json.dumps(sent[-1]["reply_markup"], ensure_ascii=False)
    tg(callback={"data": "lang:kn"})
    assert store.get_session(42)["lang"] == "kn"
    assert sent[-1]["text"].startswith("🌧️ ನೀರು")


def test_photo_then_location_runs_a_report(aws, sent, monkeypatch):
    monkeypatch.setattr(telegram, "download_file", lambda file_id: JPEG)
    calls = []

    def fake_process(image, fmt, lat, lon, lang="en", source="web"):
        calls.append((fmt, lat, lon, source))
        return {
            "status": "ok", "new_spot": False,
            "hotspot": {"id": "silk-board", "name": "Silk Board Junction"},
            "verdict": {"is_valid_photo": True, "verified": True, "is_waterlogging": True,
                        "depth": "tyre_hub", "rider_advice": "Take the flyover instead."},
        }
    monkeypatch.setattr(engine, "process_report", fake_process)

    tg({"photo": [{"file_id": "small"}, {"file_id": "large"}]})
    assert store.get_session(42)["pending_photo"] == "large"
    assert sent[-1]["reply_markup"]["keyboard"][0][0]["request_location"] is True

    tg({"location": {"latitude": 12.9173, "longitude": 77.623}})
    assert calls == [("jpeg", 12.9173, 77.623, "telegram")]
    assert "Verified: water at tyre-hub level near Silk Board Junction" in sent[-1]["text"]
    assert "Take the flyover instead." in sent[-1]["text"]
    assert sent[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == "sub:silk-board"
    assert "pending_photo" not in store.get_session(42)


def test_location_alone_lists_nearby_risk_and_subscribe_works(aws, sent, monkeypatch):
    monkeypatch.setattr(forecast, "fetch", lambda pts: [Rain([0, 0, 0], [0, 0, 0], "open-meteo")] * len(pts))
    engine.refresh_all()

    tg({"location": {"latitude": 12.9265, "longitude": 77.6810}})
    assert "Bellandur ORR" in sent[-1]["text"] and "🟢 Clear" in sent[-1]["text"]

    tg(callback={"data": "sub:bellandur-orr"})
    assert [s["chat_id"] for s in store.subscribers("bellandur-orr")] == [42]

    tg({"text": "/stop"})
    assert store.subscribers("bellandur-orr") == []


# ---------- HTTP API ----------

def call(route, body=None, headers=None, path=None):
    event = {"routeKey": route, "headers": headers or {}, "body": json.dumps(body) if body is not None else None}
    if path:
        event["pathParameters"] = path
    response = api.handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def test_hotspots_list(aws):
    status, body = call("GET /hotspots")
    assert status == 200 and len(body["hotspots"]) == 16
    assert body["storm_replay"] is None


def test_report_validation(aws):
    assert call("POST /reports", {"lat": 12.9})[0] == 400
    bad_image = base64.b64encode(b"not an image").decode()
    assert call("POST /reports", {"lat": 12.9, "lon": 77.6, "image_base64": bad_image})[0] == 400


def test_report_accepts_data_url(aws, monkeypatch):
    monkeypatch.setattr(engine, "process_report", lambda *a, **k: {"status": "ok", "args": [a[1], a[2]]})
    data_url = "data:image/jpeg;base64," + base64.b64encode(JPEG).decode()
    status, body = call("POST /reports", {"lat": 12.9, "lon": 77.6, "image_base64": data_url})
    assert status == 200 and body["args"] == ["jpeg", 12.9]


def test_admin_routes_need_the_token(aws):
    assert call("POST /admin/refresh")[0] == 403
    assert call("POST /admin/replay", {"action": "start"}, {"x-admin-token": "wrong"})[0] == 403


def test_storm_replay_start_and_stop(aws, sent):
    status, body = call("POST /admin/replay", {"action": "start", "minutes": 20}, ADMIN)
    assert status == 200 and body["refresh"]["source"] == "storm-replay"
    assert body["refresh"]["levels"]["red"] >= 1

    _, priority = call("GET /priority")
    first = priority["dispatch"][0]
    assert first["risk"]["level"] == "red" and first["rain_source"] == "storm-replay"

    _, body = call("POST /admin/replay", {"action": "stop"}, ADMIN)
    assert body["storm_replay"] is None


def test_hotspot_detail_includes_photo_links(aws, monkeypatch):
    from neeru import verifier
    monkeypatch.setattr(verifier, "verify", lambda *a, **k: {
        "is_waterlogging": True, "depth": "ankle", "confidence": 0.8, "is_valid_photo": True,
        "reason": "r", "rider_advice": "", "tools_used": [], "verified": True})
    engine.process_report(JPEG, "jpeg", 12.9172, 77.6229)
    status, body = call("GET /hotspots/{id}", path={"id": "silk-board"})
    assert status == 200 and body["reports"][0]["photo_url"].startswith("https://")
    assert call("GET /hotspots/{id}", path={"id": "nope"})[0] == 404
