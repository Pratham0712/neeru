"""The two workflows everything else calls:

refresh_all()     -- every 15 minutes (EventBridge): new rainfall -> new risk for every hotspot -> alerts
process_report()  -- a citizen photo (Telegram or web) -> verifier agent -> store -> recalibrate -> alerts
"""

import logging
import uuid

import boto3

from . import alerts, config, forecast, geo, metrics, store, verifier
from .risk import calibrate_threshold, compute_risk, dispatch_priority

log = logging.getLogger(__name__)
_s3 = None


def _s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", region_name=config.AWS_REGION)
    return _s3


def reset_clients():
    global _s3
    _s3 = None


# ---------- risk refresh ----------

def _apply_risk(hotspot: dict, past: list[float], nxt: list[float], source: str) -> dict:
    """Recompute one hotspot's risk, save it, and fire alerts on a level change."""
    reports = store.recent_reports(hotspot["id"], config.REPORT_WINDOW_HOURS)
    risk = compute_risk(hotspot, past, nxt, reports, store.now_utc(), config.REPORT_WINDOW_HOURS).as_dict()
    old_level = hotspot.get("risk", {}).get("level", "green")
    verified_recent = sum(1 for r in reports if r.get("verified") and r.get("is_waterlogging"))
    hotspot = {**hotspot, "risk": risk}
    store.update_hotspot(
        hotspot["id"],
        {
            "risk": risk,
            "rain": {"past": past, "next": nxt, "source": source},
            "verified_reports_recent": verified_recent,
            "priority": dispatch_priority(hotspot, verified_recent),
            "updated_at": store.now_utc().isoformat(),
        },
    )
    alerts.on_level_change(hotspot, old_level, risk, replay=(source == "storm-replay"))
    return risk


def refresh_all() -> dict:
    hotspots = store.list_hotspots()
    points = [(h["lat"], h["lon"]) for h in hotspots]
    replay = store.active_storm_replay()
    rains = forecast.storm_replay(points, replay) if replay else forecast.fetch(points)
    if rains is None:
        return {"updated": 0, "error": "rainfall unavailable; kept last known risk"}

    levels = {"red": 0, "amber": 0, "green": 0}
    for hotspot, rain in zip(hotspots, rains):
        risk = _apply_risk(hotspot, rain.past, rain.next, rain.source)
        levels[risk["level"]] += 1
    metrics.emit({"RedHotspots": levels["red"], "AmberHotspots": levels["amber"]})
    return {"updated": len(hotspots), "levels": levels, "source": "storm-replay" if replay else "open-meteo"}


def refresh_one(hotspot_id: str) -> dict | None:
    """Recompute one hotspot using the rain saved at the last refresh (no network call)."""
    hotspot = store.get_hotspot(hotspot_id)
    if not hotspot:
        return None
    rain = hotspot.get("rain", {"past": [0, 0, 0], "next": [0, 0, 0], "source": "open-meteo"})
    return _apply_risk(hotspot, rain["past"], rain["next"], rain.get("source", "open-meteo"))


# ---------- citizen reports ----------

def _public_hotspot(hotspot: dict | None) -> dict | None:
    """The fields of a hotspot that are safe and useful to send back to a reporter."""
    if hotspot is None:
        return None
    keys = ("id", "name", "name_kn", "lat", "lon")
    return {key: hotspot[key] for key in keys if key in hotspot}


def _new_citizen_spot(lat: float, lon: float, hotspots: list[dict], report_id: str) -> dict:
    closest = geo.nearest(lat, lon, hotspots, 1)
    near = f" near {closest[0][0]['name']}" if closest else ""
    near_kn = f"{closest[0][0].get('name_kn', closest[0][0]['name'])} ಹತ್ತಿರ " if closest else ""
    spot = {
        "id": f"citizen-{report_id[:8]}",
        "name": f"Citizen-reported spot{near}",
        "name_kn": f"{near_kn}ನಾಗರಿಕರು ವರದಿ ಮಾಡಿದ ಸ್ಥಳ",
        "lat": lat,
        "lon": lon,
        "kind": "citizen",
        "importance": 1,
        "threshold_mm": 25.0,
        "drain_hours": 1.0,
        "created_from_report": report_id,
        "created_at": store.now_utc().isoformat(),
        "risk": {"level": "green", "score": 0.0, "load_mm": 0.0, "next_mm": 0.0, "drivers": []},
    }
    store.put_hotspot(spot)
    return spot


def process_report(image_bytes: bytes, image_format: str, lat: float, lon: float,
                   lang: str = "en", source: str = "web") -> dict:
    """Verify and store a citizen photo. Returns everything the bot or web app needs to reply."""
    if not geo.in_bengaluru(lat, lon):
        return {"status": "outside_city"}

    hotspots = store.list_hotspots()
    nearby = [(h, d) for h, d in geo.nearest(lat, lon, hotspots, 1) if d <= config.NEW_SPOT_RADIUS_KM]
    hotspot = nearby[0][0] if nearby else None

    verdict = verifier.verify(image_bytes, image_format, lat, lon, hotspot, lang)
    report_id = uuid.uuid4().hex
    created_at = store.now_utc().isoformat()
    s3_key = f"reports/{created_at[:10]}/{report_id}.{image_format}"
    _s3_client().put_object(
        Bucket=config.PHOTOS_BUCKET, Key=s3_key, Body=image_bytes, ContentType=f"image/{image_format}"
    )

    new_spot = False
    if hotspot is None and verdict["verified"] and verdict["is_waterlogging"]:
        hotspot = _new_citizen_spot(lat, lon, hotspots, report_id)
        new_spot = True

    store.put_report(
        {
            "hotspot_id": hotspot["id"] if hotspot else "unmapped",
            "report_id": report_id,
            "created_at": created_at,
            "lat": lat,
            "lon": lon,
            "source": source,
            "s3_key": s3_key,
            **{k: v for k, v in verdict.items() if k != "tools_used"},
            "tools_used": ",".join(verdict.get("tools_used", [])),
        }
    )

    outcome = ("invalid" if not verdict["is_valid_photo"] else "unverified" if not verdict["verified"]
               else "flooded" if verdict["is_waterlogging"] else "dry")
    metrics.emit({"Reports": 1}, Source=source, Outcome=outcome)

    risk = None
    if hotspot and verdict["verified"]:
        old_threshold = hotspot.get("threshold_mm", 30.0)
        load = hotspot.get("risk", {}).get("load_mm", 0.0)
        new_threshold = calibrate_threshold(old_threshold, load, verdict["depth"])
        if new_threshold != old_threshold:
            store.update_hotspot(hotspot["id"], {"threshold_mm": new_threshold})
            metrics.emit({"ThresholdCalibrations": 1})
            log.info("calibrated %s threshold %.1f -> %.1f", hotspot["id"], old_threshold, new_threshold)
        risk = refresh_one(hotspot["id"])

    return {
        "status": "ok",
        "report_id": report_id,
        "hotspot": _public_hotspot(hotspot),
        "new_spot": new_spot,
        "verdict": verdict,
        "risk": risk,
    }
