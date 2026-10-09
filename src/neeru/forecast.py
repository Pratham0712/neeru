"""Hourly rainfall from Open-Meteo (free, no API key), plus a labelled storm-replay mode.

One request covers every hotspot: Open-Meteo accepts comma-separated coordinates.
For each location we ask for 3 past hours and 3 forecast hours of precipitation (mm).
"""

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .geo import distance_km

log = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HOURS = 3


@dataclass
class Rain:
    past: list[float]   # oldest -> newest, mm per hour
    next: list[float]   # soonest -> latest, mm per hour
    source: str         # "open-meteo" or "storm-replay"


def build_url(points: list[tuple[float, float]]) -> str:
    params = {
        "latitude": ",".join(f"{lat:.5f}" for lat, _ in points),
        "longitude": ",".join(f"{lon:.5f}" for _, lon in points),
        "hourly": "precipitation",
        "past_hours": HOURS,
        "forecast_hours": HOURS,
        "timezone": "Asia/Kolkata",
    }
    return f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"


def parse_response(payload, count: int) -> list[Rain]:
    """Open-Meteo returns one object for one location and a list for several."""
    items = payload if isinstance(payload, list) else [payload]
    if len(items) != count:
        raise ValueError(f"expected {count} locations, got {len(items)}")
    result = []
    for item in items:
        values = [v or 0.0 for v in item["hourly"]["precipitation"]]
        result.append(Rain(past=values[:HOURS], next=values[HOURS:HOURS * 2], source="open-meteo"))
    return result


def fetch(points: list[tuple[float, float]], timeout: float = 10.0) -> list[Rain] | None:
    """Rain for each point, or None if Open-Meteo could not be reached."""
    if not points:
        return []
    try:
        with urllib.request.urlopen(build_url(points), timeout=timeout) as response:
            return parse_response(json.load(response), len(points))
    except Exception:  # network errors, bad JSON, shape changes: keep the last known risk
        log.exception("Open-Meteo fetch failed")
        return None


def storm_replay(points: list[tuple[float, float]], scenario: dict) -> list[Rain]:
    """Synthetic storm for demos, clearly labelled as such everywhere it appears.

    A cloudburst centred on scenario["lat"], scenario["lon"]: intensity peaks at
    scenario["peak_mm_hr"] at the centre and fades to zero at scenario["radius_km"].
    """
    peak = float(scenario.get("peak_mm_hr", 40))
    radius = float(scenario.get("radius_km", 8))
    shape_past = [0.2, 0.5, 0.9]
    shape_next = [1.0, 0.7, 0.3]
    result = []
    for lat, lon in points:
        d = distance_km(lat, lon, float(scenario["lat"]), float(scenario["lon"]))
        k = max(0.0, 1.0 - d / radius) * peak
        result.append(
            Rain(
                past=[round(k * s, 2) for s in shape_past],
                next=[round(k * s, 2) for s in shape_next],
                source="storm-replay",
            )
        )
    return result
