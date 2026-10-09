"""Safe Route: which way should I ride right now?

1. Ask OSRM (open-source routing on OpenStreetMap roads) for the fastest route
   and up to 2 alternatives between two points.
2. For every route, find the flood hotspots it passes within PASS_RADIUS_KM.
3. Rank the routes: fewer red spots first, then fewer amber spots, then the
   lowest peak risk, then the shortest time.
4. Explain the trade-off in plain words: "the fastest route crosses X; the safer
   one takes N more minutes and avoids every red spot".

All the maths is pure Python on short polylines, so a route check stays fast
inside Lambda and can be tested without a network.
"""

import json
import logging
import math
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
PASS_RADIUS_KM = 0.35   # a route "passes" a hotspot if it comes this close
USER_AGENT = "Neeru/1.0 (Environmental Hacks 2026 student project)"


# ---------- geometry ----------

def _to_xy_km(lat: float, lon: float, ref_lat: float) -> tuple[float, float]:
    """Project to a flat km grid around ref_lat. Accurate to metres over a city."""
    x = math.radians(lon) * 6371.0088 * math.cos(math.radians(ref_lat))
    y = math.radians(lat) * 6371.0088
    return x, y


def distance_to_polyline_km(lat: float, lon: float, line: list[list[float]]) -> float:
    """Shortest distance from a point to a polyline of [lon, lat] pairs (GeoJSON order).

    For each segment A->B: project the point P onto the segment, clamp to the
    ends, and measure P to that closest point. The minimum over all segments wins.
    """
    px, py = _to_xy_km(lat, lon, lat)
    best = float("inf")
    for (lon_a, lat_a), (lon_b, lat_b) in zip(line, line[1:]):
        ax, ay = _to_xy_km(lat_a, lon_a, lat)
        bx, by = _to_xy_km(lat_b, lon_b, lat)
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        t = 0.0 if length_sq == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
        cx, cy = ax + t * dx, ay + t * dy
        best = min(best, math.hypot(px - cx, py - cy))
    if len(line) == 1:
        ax, ay = _to_xy_km(line[0][1], line[0][0], lat)
        best = math.hypot(px - ax, py - ay)
    return best


# ---------- scoring ----------

def score_route(route: dict, hotspots: list[dict], radius_km: float = PASS_RADIUS_KM) -> dict:
    """Annotate one OSRM route with the hotspots it passes and its worst risk."""
    line = route["geometry"]["coordinates"]
    passes = []
    for hotspot in hotspots:
        distance = distance_to_polyline_km(hotspot["lat"], hotspot["lon"], line)
        if distance <= radius_km:
            risk = hotspot.get("risk", {})
            passes.append({
                "id": hotspot["id"],
                "name": hotspot["name"],
                "name_kn": hotspot.get("name_kn"),
                "lat": hotspot["lat"],
                "lon": hotspot["lon"],
                "level": risk.get("level", "green"),
                "score": risk.get("score", 0.0),
                "distance_km": round(distance, 3),
            })
    passes.sort(key=lambda p: p["score"], reverse=True)
    return {
        "distance_km": round(route["distance"] / 1000, 2),
        "duration_min": round(route["duration"] / 60, 1),
        "geometry": line,
        "passes": passes,
        "red": sum(1 for p in passes if p["level"] == "red"),
        "amber": sum(1 for p in passes if p["level"] == "amber"),
        "max_score": max((p["score"] for p in passes), default=0.0),
    }


def rank_key(scored: dict) -> tuple:
    return (scored["red"], scored["amber"], round(scored["max_score"], 2), scored["duration_min"])


def plan(routes: list[dict], hotspots: list[dict]) -> dict:
    """Score every route, pick the safest, and explain the choice."""
    if not routes:
        return {"routes": [], "recommended": None, "verdict": "no_route"}

    scored = [score_route(r, hotspots) for r in routes]
    for index, s in enumerate(scored):
        s["index"] = index
        s["is_fastest"] = False
    fastest = min(scored, key=lambda s: s["duration_min"])
    fastest["is_fastest"] = True
    best = min(scored, key=rank_key)

    # clear         -> the fastest route is already free of amber and red spots
    # detour_clear  -> a slower route avoids every amber and red spot
    # caution       -> the best route still passes amber spots, but no red ones
    # no_safe_route -> every route passes at least one red spot
    if best["red"] == 0 and best["amber"] == 0:
        verdict = "clear" if best is fastest else "detour_clear"
    elif best["red"] == 0:
        verdict = "caution"
    else:
        verdict = "no_safe_route"

    return {
        "routes": scored,
        "recommended": best["index"],
        "fastest": fastest["index"],
        "verdict": verdict,
        "extra_min": round(best["duration_min"] - fastest["duration_min"], 1),
        "avoided": [p for p in fastest["passes"] if p["level"] in ("red", "amber")
                    and p["id"] not in {q["id"] for q in best["passes"]}],
    }


# ---------- OSRM ----------

def build_url(origin: tuple[float, float], destination: tuple[float, float]) -> str:
    (lat1, lon1), (lat2, lon2) = origin, destination
    coords = f"{lon1:.6f},{lat1:.6f};{lon2:.6f},{lat2:.6f}"
    query = urllib.parse.urlencode({"alternatives": 2, "overview": "full", "geometries": "geojson"})
    return f"{OSRM_URL}/{coords}?{query}"


def fetch_routes(origin: tuple[float, float], destination: tuple[float, float],
                 timeout: float = 8.0) -> list[dict] | None:
    """Routes from OSRM, or None if it could not be reached."""
    request = urllib.request.Request(build_url(origin, destination), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except Exception:
        log.exception("OSRM request failed")
        return None
    if payload.get("code") != "Ok":
        log.warning("OSRM returned %s", payload.get("code"))
        return []
    return payload.get("routes", [])
