from urllib.parse import parse_qs, urlparse

import pytest

from neeru import forecast


def test_url_batches_all_points():
    query = parse_qs(urlparse(forecast.build_url([(12.9, 77.6), (13.0, 77.7)])).query)
    assert query["latitude"] == ["12.90000,13.00000"]
    assert query["longitude"] == ["77.60000,77.70000"]
    assert query["past_hours"] == ["3"] and query["forecast_hours"] == ["3"]


def test_parse_single_location_object():
    payload = {"hourly": {"precipitation": [0.1, 0.2, 0.3, 4.0, None, 6.0]}}
    rain = forecast.parse_response(payload, 1)[0]
    assert rain.past == [0.1, 0.2, 0.3]
    assert rain.next == [4.0, 0.0, 6.0]  # nulls become 0


def test_parse_list_and_count_check():
    payload = [{"hourly": {"precipitation": [0] * 6}}] * 2
    assert len(forecast.parse_response(payload, 2)) == 2
    with pytest.raises(ValueError):
        forecast.parse_response(payload, 3)


def test_fetch_returns_none_when_offline(monkeypatch):
    def boom(*_a, **_k):
        raise OSError("no network")
    monkeypatch.setattr(forecast.urllib.request, "urlopen", boom)
    assert forecast.fetch([(12.9, 77.6)]) is None


def test_storm_replay_is_strongest_at_centre_and_labelled():
    scenario = {"lat": 12.93, "lon": 77.68, "peak_mm_hr": 40, "radius_km": 8}
    centre, far = forecast.storm_replay([(12.93, 77.68), (13.2, 77.4)], scenario)
    assert centre.next[0] == 40
    assert far.next == [0, 0, 0]
    assert centre.source == "storm-replay"
