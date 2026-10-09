"""Small geography helpers. No external dependencies."""

import math

EARTH_RADIUS_KM = 6371.0088


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometres (haversine formula)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest(lat: float, lon: float, hotspots: list[dict], limit: int = 1) -> list[tuple[dict, float]]:
    """Return the `limit` hotspots closest to (lat, lon) as (hotspot, distance_km) pairs."""
    ranked = sorted(
        ((h, distance_km(lat, lon, h["lat"], h["lon"])) for h in hotspots),
        key=lambda pair: pair[1],
    )
    return ranked[:limit]


def in_bengaluru(lat: float, lon: float) -> bool:
    """Rough bounding box for Bengaluru Urban, used to reject obviously wrong locations."""
    return 12.70 <= lat <= 13.30 and 77.30 <= lon <= 77.95
