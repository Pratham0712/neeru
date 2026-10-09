"""End-to-end workflows on fake AWS: refresh -> alerts, and report -> calibrate -> alerts."""

from neeru import engine, forecast, store, verifier
from neeru.forecast import Rain
from tests.conftest import JPEG


def dry_everywhere(points):
    return [Rain(past=[0, 0, 0], next=[0, 0, 0], source="open-meteo") for _ in points]


def storm_at_silk_board(points):
    return [
        Rain(past=[2, 5, 10], next=[20, 10, 2], source="open-meteo") if abs(lat - 12.9172) < 1e-3
        else Rain(past=[0, 0, 0], next=[0, 0, 0], source="open-meteo")
        for lat, _lon in points
    ]


def fake_verdict(depth="tyre_hub", confidence=0.9, valid=True):
    def verify(image_bytes, image_format, lat, lon, hotspot, lang="en"):
        return {
            "is_waterlogging": depth != "none", "depth": depth, "confidence": confidence,
            "is_valid_photo": valid, "reason": "test", "rider_advice": "Avoid.",
            "tools_used": ["get_rainfall_here", "submit_verdict"],
            "verified": valid and confidence >= 0.6,
        }
    return verify


def test_refresh_computes_risk_and_alerts_subscribers(aws, sent, monkeypatch):
    monkeypatch.setattr(forecast, "fetch", storm_at_silk_board)
    store.subscribe("silk-board", 111, "kn")

    summary = engine.refresh_all()

    assert summary["levels"]["red"] == 1
    assert store.get_hotspot("silk-board")["risk"]["level"] == "red"
    assert len(sent) == 1 and sent[0]["chat_id"] == 111
    assert "ಸಿಲ್ಕ್ ಬೋರ್ಡ್" in sent[0]["text"]  # Kannada subscriber gets Kannada

    # a second refresh with the same rain does not alert again
    engine.refresh_all()
    assert len(sent) == 1


def test_refresh_keeps_last_risk_when_rain_unavailable(aws, monkeypatch):
    monkeypatch.setattr(forecast, "fetch", lambda points: None)
    assert engine.refresh_all()["updated"] == 0


def test_storm_replay_is_labelled_in_alerts(aws, sent, monkeypatch):
    from datetime import timedelta
    store.put_settings({"storm_replay": {
        "lat": 12.926, "lon": 77.681, "peak_mm_hr": 45, "radius_km": 9,
        "until": (store.now_utc() + timedelta(minutes=30)).isoformat(),
    }})
    store.subscribe("bellandur-orr", 222, "en")
    summary = engine.refresh_all()
    assert summary["source"] == "storm-replay"
    assert summary["levels"]["red"] >= 1
    assert "(storm replay demo)" in sent[0]["text"]


def test_verified_report_lowers_threshold_and_turns_spot_amber(aws, sent, monkeypatch):
    monkeypatch.setattr(forecast, "fetch", dry_everywhere)
    engine.refresh_all()
    monkeypatch.setattr(verifier, "verify", fake_verdict("tyre_hub"))

    result = engine.process_report(JPEG, "jpeg", 12.9173, 77.6230, source="telegram")

    assert result["hotspot"]["id"] == "silk-board"
    assert result["verdict"]["verified"]
    spot = store.get_hotspot("silk-board")
    assert spot["threshold_mm"] < 26          # calibrated down from the seed value
    assert spot["risk"]["level"] == "amber"     # a single fresh tyre-hub report
    assert len(store.recent_reports("silk-board", 1)) == 1


def test_knee_deep_report_turns_spot_red_and_alerts(aws, sent, monkeypatch):
    monkeypatch.setattr(forecast, "fetch", dry_everywhere)
    engine.refresh_all()
    store.subscribe("kr-circle", 333, "en")
    monkeypatch.setattr(verifier, "verify", fake_verdict("knee"))

    engine.process_report(JPEG, "jpeg", 12.9766, 77.5875)

    assert store.get_hotspot("kr-circle")["risk"]["level"] == "red"
    assert any(m["chat_id"] == 333 and "Flood alert" in m["text"] for m in sent)


def test_report_far_from_known_spots_creates_a_citizen_spot(aws, monkeypatch):
    monkeypatch.setattr(verifier, "verify", fake_verdict("ankle"))
    result = engine.process_report(JPEG, "jpeg", 13.10, 77.58)  # Yelahanka side, not seeded
    assert result["new_spot"] is True
    assert result["hotspot"]["id"].startswith("citizen-")
    assert store.get_hotspot(result["hotspot"]["id"])["kind"] == "citizen"


def test_unverified_far_report_does_not_create_a_spot(aws, monkeypatch):
    monkeypatch.setattr(verifier, "verify", fake_verdict("knee", confidence=0.3))
    result = engine.process_report(JPEG, "jpeg", 13.10, 77.58)
    assert result["new_spot"] is False and result["hotspot"] is None


def test_reports_outside_bengaluru_are_rejected(aws):
    assert engine.process_report(JPEG, "jpeg", 19.07, 72.87)["status"] == "outside_city"
