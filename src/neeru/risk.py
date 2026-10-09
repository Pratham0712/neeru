"""The flood-risk model. Pure functions only, so every number on the map can be explained.

How a hotspot's risk is computed
--------------------------------
1. Rain load (mm): water that is still on the road plus water about to arrive.
     * Rain from the past 3 hours counts, but it decays as the drain clears it.
       Each hotspot has a `drain_hours` half-life: after that many hours, half of
       that rain is assumed to have drained away.
     * Rain forecast for the next 3 hours counts in full.
2. Rain ratio = rain load / the hotspot's `threshold_mm` (the load at which this spot floods).
3. Citizen evidence: a verified photo report sets a floor on the score, so a
   flooded underpass shows red even if the forecast missed a local cloudburst.
   That floor fades over REPORT_WINDOW_HOURS.
4. score = max(rain ratio, report floor)
     score >= 1.0 -> red   (avoid)
     score >= 0.5 -> amber (caution)
     otherwise    -> green

Self-calibration: when citizens report a flood at a spot whose threshold said it
should be dry, that threshold comes down. When they report it dry during heavy
rain, it goes up a little. The map gets more accurate the more people use it.
"""

from dataclasses import dataclass, field
from datetime import datetime

# Depth vocabulary shared by the verifier agent, the bot and the web app.
DEPTHS = ("none", "ankle", "tyre_hub", "knee")

# The floor a fresh verified report puts on a hotspot's score.
DEPTH_FLOOR = {"none": 0.0, "ankle": 0.6, "tyre_hub": 1.0, "knee": 1.4}

RED_AT = 1.0
AMBER_AT = 0.5

MIN_THRESHOLD_MM = 8.0
MAX_THRESHOLD_MM = 90.0


@dataclass
class RiskResult:
    score: float
    level: str
    load_mm: float
    past_mm: float
    next_mm: float
    peak_next_mm_hr: float
    drivers: list[str] = field(default_factory=list)
    report_depth: str | None = None  # set when a citizen report drives the score

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 3),
            "level": self.level,
            "load_mm": round(self.load_mm, 2),
            "past_mm": round(self.past_mm, 2),
            "next_mm": round(self.next_mm, 2),
            "peak_next_mm_hr": round(self.peak_next_mm_hr, 2),
            "drivers": self.drivers,
            "report_depth": self.report_depth,
        }


def level_for(score: float) -> str:
    if score >= RED_AT:
        return "red"
    if score >= AMBER_AT:
        return "amber"
    return "green"


def rain_load(past_hourly: list[float], next_hourly: list[float], drain_hours: float) -> float:
    """Rain load in mm.

    past_hourly is ordered oldest -> newest. The newest hour is half an hour old
    on average, the one before it 1.5 hours old, and so on.

    Example with drain_hours = 1:
        past [4, 4, 4], next [10, 0, 0]
        past weights: newest 0.5**0.5 = 0.707, then 0.5**1.5 = 0.354, then 0.5**2.5 = 0.177
        load = 4*0.707 + 4*0.354 + 4*0.177 + 10 = 14.95 mm
    """
    drain_hours = max(drain_hours, 0.1)
    load = 0.0
    for hours_ago_index, mm in enumerate(reversed(past_hourly)):
        age_hours = hours_ago_index + 0.5
        load += max(mm, 0.0) * 0.5 ** (age_hours / drain_hours)
    load += sum(max(mm, 0.0) for mm in next_hourly)
    return load


def report_floor(reports: list[dict], now: datetime, window_hours: float) -> tuple[float, dict | None]:
    """Strongest score floor from verified reports, fading linearly to half over the window.

    Returns (floor, the report that set it).
    """
    best, best_report = 0.0, None
    for report in reports:
        if not report.get("verified"):
            continue
        age_hours = (now - datetime.fromisoformat(report["created_at"])).total_seconds() / 3600
        if age_hours < 0 or age_hours > window_hours:
            continue
        fade = 1.0 - 0.5 * (age_hours / window_hours)
        floor = DEPTH_FLOOR.get(report.get("depth", "none"), 0.0) * fade
        if floor > best:
            best, best_report = floor, report
    return best, best_report


def compute_risk(
    hotspot: dict,
    past_hourly: list[float],
    next_hourly: list[float],
    reports: list[dict],
    now: datetime,
    window_hours: float = 2.0,
) -> RiskResult:
    """Combine rainfall and citizen reports into one score for a hotspot."""
    load = rain_load(past_hourly, next_hourly, hotspot.get("drain_hours", 1.0))
    ratio = load / max(hotspot.get("threshold_mm", 30.0), MIN_THRESHOLD_MM)
    floor, floor_report = report_floor(reports, now, window_hours)
    score = max(ratio, floor)

    drivers = []
    report_depth = None
    past_mm, next_mm = sum(past_hourly), sum(next_hourly)
    peak = max(next_hourly) if next_hourly else 0.0
    if next_mm >= 1:
        drivers.append(f"{next_mm:.0f} mm rain forecast in the next 3 h")
    if past_mm >= 1:
        drivers.append(f"{past_mm:.0f} mm fell in the last 3 h")
    if floor_report is not None and floor >= ratio:
        report_depth = floor_report["depth"]
        drivers.append(f"citizen photo: water at {report_depth.replace('_', ' ')} level")
    if not drivers:
        drivers.append("no significant rain")

    return RiskResult(
        score=score,
        level=level_for(score),
        load_mm=load,
        past_mm=past_mm,
        next_mm=next_mm,
        peak_next_mm_hr=peak,
        drivers=drivers,
        report_depth=report_depth,
    )


def calibrate_threshold(threshold_mm: float, load_at_report_mm: float, depth: str) -> float:
    """Nudge a hotspot's flood threshold using a verified citizen report.

    * Flooded (tyre-hub or deeper) while the model expected dry -> lower the threshold
      to just above the load that actually flooded it, moving at most 25% per report.
    * Dry while the model expected a flood -> raise the threshold by 5%.
    * Otherwise the model agreed with the citizen, so nothing changes.
    """
    flooded = DEPTH_FLOOR.get(depth, 0.0) >= DEPTH_FLOOR["tyre_hub"]
    if flooded and load_at_report_mm < threshold_mm:
        target = max(load_at_report_mm * 1.1, threshold_mm * 0.75)
        return round(max(MIN_THRESHOLD_MM, min(threshold_mm, target)), 2)
    if depth == "none" and load_at_report_mm > threshold_mm * 1.2:
        return round(min(MAX_THRESHOLD_MM, threshold_mm * 1.05), 2)
    return threshold_mm


def dispatch_priority(hotspot: dict, verified_reports_recent: int) -> float:
    """Order for ward engineers: where should pumps and traffic police go first?

    Risk score x road importance (1 = local road, 3 = arterial or underpass),
    boosted 25% for each recent verified citizen report.
    """
    score = hotspot.get("risk", {}).get("score", 0.0)
    importance = hotspot.get("importance", 1)
    return round(score * importance * (1 + 0.25 * verified_reports_recent), 3)
