"""Public HTTP API for the web app (API Gateway HTTP API, payload format 2.0).

GET  /hotspots          every hotspot with its current risk (the map)
GET  /hotspots/{id}     one hotspot plus recent citizen reports with photo links
GET  /priority          dispatch list for ward engineers, most urgent first
POST /reports           a citizen photo from the web app: {lat, lon, image_base64, lang}
GET  /route             Safe Route: ?from=lat,lon&to=lat,lon -> routes ranked by flood risk
POST /ops/briefing      Ops Copilot dispatch briefing (cached; {"force": true} regenerates)
POST /admin/replay      start/stop a labelled storm replay (header x-admin-token)
POST /admin/refresh     recompute all risk now (header x-admin-token)
"""

import base64
import binascii
import hmac
import json
import logging
from datetime import timedelta

import boto3

from neeru import briefing, config, engine, geo, images, metrics, routing, store

log = logging.getLogger()
log.setLevel(logging.INFO)

_s3 = boto3.client("s3", region_name=config.AWS_REGION)

PUBLIC_FIELDS = (
    "id", "name", "name_kn", "lat", "lon", "kind", "importance", "threshold_mm",
    "risk", "priority", "verified_reports_recent", "updated_at",
)


def respond(status: int, body: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def public(hotspot: dict) -> dict:
    data = {key: hotspot[key] for key in PUBLIC_FIELDS if key in hotspot}
    rain = hotspot.get("rain", {})
    data["rain_source"] = rain.get("source", "open-meteo")
    data["rain_past"] = rain.get("past", [])
    data["rain_next"] = rain.get("next", [])
    return data


def read_json(event: dict) -> dict:
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode()
    return json.loads(body)


def is_admin(event: dict) -> bool:
    supplied = (event.get("headers") or {}).get("x-admin-token", "")
    return bool(config.ADMIN_TOKEN) and hmac.compare_digest(supplied, config.ADMIN_TOKEN)


def list_hotspots(_event):
    hotspots = sorted(store.list_hotspots(), key=lambda h: h.get("risk", {}).get("score", 0), reverse=True)
    return respond(200, {
        "hotspots": [public(h) for h in hotspots],
        "storm_replay": store.active_storm_replay(),
        "generated_at": store.now_utc().isoformat(),
    })


def get_hotspot(event):
    hotspot_id = event["pathParameters"]["id"]
    hotspot = store.get_hotspot(hotspot_id)
    if not hotspot:
        return respond(404, {"error": "not found"})
    reports = []
    for report in store.recent_reports(hotspot_id, hours=6)[:20]:
        photo_url = _s3.generate_presigned_url(
            "get_object", Params={"Bucket": config.PHOTOS_BUCKET, "Key": report["s3_key"]}, ExpiresIn=600
        )
        reports.append({
            "created_at": report["created_at"],
            "verified": report.get("verified", False),
            "depth": report.get("depth"),
            "confidence": report.get("confidence"),
            "reason": report.get("reason"),
            "source": report.get("source"),
            "photo_url": photo_url,
        })
    return respond(200, {"hotspot": public(hotspot), "reports": reports})


def priority(_event):
    hotspots = [h for h in store.list_hotspots() if h.get("risk", {}).get("level") in ("red", "amber")]
    hotspots.sort(key=lambda h: h.get("priority", 0), reverse=True)
    return respond(200, {"dispatch": [public(h) for h in hotspots], "generated_at": store.now_utc().isoformat()})


def create_report(event):
    try:
        body = read_json(event)
        lat, lon = float(body["lat"]), float(body["lon"])
        image = base64.b64decode(body["image_base64"].split(",")[-1], validate=True)
    except (KeyError, ValueError, TypeError, binascii.Error, json.JSONDecodeError):
        return respond(400, {"error": "send lat, lon and image_base64"})

    image_format = images.detect_format(image)
    if image_format is None:
        return respond(400, {"error": "image must be JPEG, PNG or WebP"})
    if len(image) > images.MAX_IMAGE_BYTES:
        return respond(413, {"error": "image too large; resize to under 3.5 MB"})

    lang = body.get("lang", "en") if body.get("lang") in ("en", "kn") else "en"
    result = engine.process_report(image, image_format, lat, lon, lang=lang, source="web")
    if result["status"] == "outside_city":
        return respond(422, {"error": "Neeru covers Bengaluru only for now", **result})
    return respond(200, result)


def admin_replay(event):
    if not is_admin(event):
        return respond(403, {"error": "forbidden"})
    body = read_json(event)
    settings = store.get_settings()
    if body.get("action") == "stop":
        settings.pop("storm_replay", None)
    else:
        minutes = int(body.get("minutes", 30))
        settings["storm_replay"] = {
            "lat": float(body.get("lat", 12.9352)),       # default: Bellandur / ORR
            "lon": float(body.get("lon", 77.6800)),
            "peak_mm_hr": float(body.get("peak_mm_hr", 35)),
            "radius_km": float(body.get("radius_km", 6)),
            "until": (store.now_utc() + timedelta(minutes=minutes)).isoformat(),
        }
    store.put_settings(settings)
    return respond(200, {"storm_replay": store.active_storm_replay(), "refresh": engine.refresh_all()})


def admin_refresh(event):
    if not is_admin(event):
        return respond(403, {"error": "forbidden"})
    return respond(200, engine.refresh_all())


def parse_point(text: str | None) -> tuple[float, float] | None:
    """'12.93,77.62' -> (12.93, 77.62), or None if it is not a point in Bengaluru."""
    try:
        lat, lon = (float(part) for part in (text or "").split(","))
    except ValueError:
        return None
    return (lat, lon) if geo.in_bengaluru(lat, lon) else None


def safe_route(event):
    params = event.get("queryStringParameters") or {}
    origin, destination = parse_point(params.get("from")), parse_point(params.get("to"))
    if not origin or not destination:
        return respond(400, {"error": "from and to must be lat,lon points inside Bengaluru"})
    if geo.distance_km(*origin, *destination) < 0.2:
        return respond(400, {"error": "start and destination are too close"})

    routes = routing.fetch_routes(origin, destination)
    if routes is None:
        return respond(502, {"error": "route service unavailable, try again in a minute"})
    result = routing.plan(routes, store.list_hotspots())
    metrics.emit({"RouteChecks": 1}, Verdict=result["verdict"])
    return respond(200, {**result, "storm_replay": store.active_storm_replay()})


def ops_briefing(event):
    body = read_json(event)
    force = bool(body.get("force")) and is_admin(event)  # anyone can read; only admins can force a new one
    return respond(200, briefing.get_briefing(force=force))


ROUTES = {
    "GET /route": safe_route,
    "POST /ops/briefing": ops_briefing,
    "GET /hotspots": list_hotspots,
    "GET /hotspots/{id}": get_hotspot,
    "GET /priority": priority,
    "POST /reports": create_report,
    "POST /admin/replay": admin_replay,
    "POST /admin/refresh": admin_refresh,
}


def handler(event, _context):
    route = ROUTES.get(event.get("routeKey", ""))
    if route is None:
        return respond(404, {"error": "unknown route"})
    try:
        return route(event)
    except Exception:
        log.exception("request failed")
        return respond(500, {"error": "internal error"})
