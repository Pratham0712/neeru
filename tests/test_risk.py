from datetime import datetime, timedelta, timezone

import pytest

from neeru.risk import (
    calibrate_threshold,
    compute_risk,
    dispatch_priority,
    level_for,
    rain_load,
    report_floor,
)

NOW = datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc)
SPOT = {"id": "x", "threshold_mm": 20.0, "drain_hours": 1.0, "importance": 3}


def test_rain_load_matches_docstring_example():
    assert rain_load([4, 4, 4], [10, 0, 0], drain_hours=1.0) == pytest.approx(14.95, abs=0.01)


def test_old_rain_counts_less_than_fresh_rain():
    old = rain_load([10, 0, 0], [0, 0, 0], drain_hours=1.0)
    fresh = rain_load([0, 0, 10], [0, 0, 0], drain_hours=1.0)
    assert fresh > old


def test_slow_drains_hold_more_water():
    assert rain_load([10, 10, 10], [], drain_hours=3.0) > rain_load([10, 10, 10], [], drain_hours=0.5)


@pytest.mark.parametrize("score, level", [(0.0, "green"), (0.49, "green"), (0.5, "amber"), (1.0, "red"), (2.3, "red")])
def test_levels(score, level):
    assert level_for(score) == level


def test_heavy_forecast_turns_spot_red():
    risk = compute_risk(SPOT, [0, 0, 0], [15, 10, 0], [], NOW)
    assert risk.level == "red"
    assert "25 mm rain forecast" in risk.drivers[0]


def test_dry_day_is_green():
    risk = compute_risk(SPOT, [0, 0, 0], [0, 0, 0], [], NOW)
    assert risk.level == "green"
    assert risk.drivers == ["no significant rain"]


def report(depth, minutes_ago, verified=True):
    return {
        "depth": depth,
        "verified": verified,
        "created_at": (NOW - timedelta(minutes=minutes_ago)).isoformat(),
    }


def test_verified_report_overrides_dry_forecast():
    # tyre-hub floor is 1.0, faded slightly after 5 minutes -> ~0.98, so amber
    risk = compute_risk(SPOT, [0, 0, 0], [0, 0, 0], [report("tyre_hub", 5)], NOW)
    assert risk.level == "amber"
    assert risk.score == pytest.approx(0.979, abs=0.001)
    assert risk.report_depth == "tyre_hub"


def test_fresh_knee_deep_report_is_red():
    risk = compute_risk(SPOT, [0, 0, 0], [0, 0, 0], [report("knee", 1)], NOW)
    assert risk.level == "red"


def test_unverified_and_stale_reports_are_ignored():
    floor, _ = report_floor([report("knee", 5, verified=False), report("knee", 300)], NOW, window_hours=2)
    assert floor == 0.0


def test_report_floor_fades_to_half_over_window():
    fresh, _ = report_floor([report("knee", 0)], NOW, 2)
    old, _ = report_floor([report("knee", 119)], NOW, 2)
    assert fresh == pytest.approx(1.4)
    assert old == pytest.approx(0.7, abs=0.01)


def test_calibration_lowers_threshold_when_citizens_see_flooding():
    # model expected 10 mm to be safe at a 20 mm threshold, but it flooded
    assert calibrate_threshold(20.0, 10.0, "tyre_hub") == 15.0  # capped at a 25% move
    assert calibrate_threshold(20.0, 17.0, "knee") == pytest.approx(18.7)


def test_calibration_raises_threshold_when_citizens_see_dry_road_in_heavy_rain():
    assert calibrate_threshold(20.0, 30.0, "none") == 21.0


def test_calibration_leaves_agreeing_reports_alone():
    assert calibrate_threshold(20.0, 25.0, "knee") == 20.0
    assert calibrate_threshold(20.0, 5.0, "none") == 20.0
    assert calibrate_threshold(20.0, 5.0, "ankle") == 20.0


def test_calibration_stays_within_bounds():
    assert calibrate_threshold(9.0, 0.0, "knee") == 8.0


def test_dispatch_priority_prefers_important_reported_spots():
    hot = {**SPOT, "risk": {"score": 1.2}}
    minor = {**SPOT, "importance": 1, "risk": {"score": 1.2}}
    assert dispatch_priority(hot, 2) > dispatch_priority(hot, 0) > dispatch_priority(minor, 0)
