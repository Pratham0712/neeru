"""Safe Route: geometry, scoring, ranking and the API endpoint."""

import json

import pytest

from handlers import api
from neeru import routing

SILK_BOARD = {"id": "silk-board", "name": "Silk Board Junction", "lat": 12.9172, "lon": 77.6229,
              "risk": {"level": "red", "score": 1.4}}
HSR = {"id": "hsr", "name": "HSR", "lat": 12.9200, "lon": 77.6440, "risk": {"level": "amber", "score": 0.7}}
FAR = {"id": "far", "name": "Far away", "lat": 13.05, "lon": 77.50, "risk": {"level": "red", "score": 2.0}}


def route(points, minutes, km=5.0):
    """An OSRM-shaped route through (lat, lon) points."""
    return {"duration": minutes * 60, "distance": km * 1000,
            "geometry": {"coordinates": [[lon, lat] for lat, lon in points]}}


# straight east-west line through Silk Board, and a detour 2 km south of it
THROUGH_SILK_BOARD = route([(12.9172, 77.60), (12.9172, 77.65)], minutes=20)
DETOUR_SOUTH = route([(12.9172, 77.60), (12.899, 77.60), (12.899, 77.65), (12.9172, 77.65)], minutes=27)


def test_distance_to_a_point_on_the_line_is_zero():
    assert routing.distance_to_polyline_km(12.9172, 77.6229, [[77.60, 12.9172], [77.65, 12.9172]]) < 0.001


def test_distance_to_a_point_beside_the_line():
    # 0.01 degrees of latitude is about 1.11 km
    d = routing.distance_to_polyline_km(12.9272, 77.6229, [[77.60, 12.9172], [77.65, 12.9172]])
    assert d == pytest.approx(1.112, abs=0.01)


def test_distance_beyond_the_end_uses_the_endpoint():
    d = routing.distance_to_polyline_km(12.9172, 77.66, [[77.60, 12.9172], [77.65, 12.9172]])
    assert d == pytest.approx(1.084, abs=0.01)  # 0.01 deg of longitude at 12.9 N


def test_score_route_finds_only_nearby_spots():
    scored = routing.score_route(THROUGH_SILK_BOARD, [SILK_BOARD, FAR])
    assert [p["id"] for p in scored["passes"]] == ["silk-board"]
    assert scored["red"] == 1 and scored["duration_min"] == 20


def test_plan_recommends_the_detour_and_explains_it():
    result = routing.plan([THROUGH_SILK_BOARD, DETOUR_SOUTH], [SILK_BOARD, FAR])
    assert result["fastest"] == 0
    assert result["recommended"] == 1
    assert result["verdict"] == "detour_clear"
    assert result["extra_min"] == 7
    assert [p["id"] for p in result["avoided"]] == ["silk-board"]


def test_plan_keeps_the_fastest_route_when_it_is_clear():
    result = routing.plan([DETOUR_SOUTH, THROUGH_SILK_BOARD], [FAR])
    assert result["recommended"] == result["fastest"] == 1
    assert result["verdict"] == "clear" and result["extra_min"] == 0


def test_plan_prefers_amber_over_red_and_reports_caution():
    amber_route = route([(12.9200, 77.63), (12.9200, 77.66)], minutes=30)
    result = routing.plan([THROUGH_SILK_BOARD, amber_route], [SILK_BOARD, HSR])
    assert result["recommended"] == 1 and result["verdict"] == "caution"


def test_plan_when_every_route_is_red():
    result = routing.plan([THROUGH_SILK_BOARD], [SILK_BOARD])
    assert result["verdict"] == "no_safe_route"


def test_plan_with_no_routes():
    assert routing.plan([], [SILK_BOARD])["verdict"] == "no_route"


def test_osrm_url_uses_lon_lat_order():
    url = routing.build_url((12.9, 77.6), (13.0, 77.7))
    assert "/77.600000,12.900000;77.700000,13.000000?" in url
    assert "alternatives=2" in url and "geometries=geojson" in url


# ---------- API ----------

def call_route(query):
    response = api.handler({"routeKey": "GET /route", "queryStringParameters": query, "headers": {}}, None)
    return response["statusCode"], json.loads(response["body"])


def test_route_endpoint_validates_points(aws):
    assert call_route({"from": "12.9,77.6"})[0] == 400
    assert call_route({"from": "19.07,72.87", "to": "12.9,77.6"})[0] == 400   # Mumbai
    assert call_route({"from": "12.9,77.6", "to": "12.9001,77.6001"})[0] == 400  # too close


def test_route_endpoint_ranks_routes(aws, monkeypatch):
    from neeru import store
    store.update_hotspot("silk-board", {"risk": {"level": "red", "score": 1.5}})
    monkeypatch.setattr(routing, "fetch_routes", lambda o, d: [THROUGH_SILK_BOARD, DETOUR_SOUTH])
    status, body = call_route({"from": "12.9172,77.60", "to": "12.9172,77.65"})
    assert status == 200
    assert body["verdict"] == "detour_clear" and body["recommended"] == 1
    assert body["avoided"][0]["name"] == "Silk Board Junction"


def test_route_endpoint_reports_routing_outage(aws, monkeypatch):
    monkeypatch.setattr(routing, "fetch_routes", lambda o, d: None)
    assert call_route({"from": "12.9172,77.60", "to": "12.9172,77.65"})[0] == 502
