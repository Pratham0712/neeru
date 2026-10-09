"""Ops Copilot: the second agent. Writes a dispatch briefing for ward engineers.

The verifier agent decides "is this photo real and how deep is the water".
This agent answers the engineer's question: "I have a few pumps and a few
traffic constables. Where do they go first, and what do I tell them?"

Tools:
  get_dispatch_list    -- red/amber spots ranked by priority, with the reasons
  get_spot_reports     -- recent verified citizen reports at one spot
  submit_briefing      -- the final, structured briefing (English + Kannada)

Briefings are cached: the same situation is not re-generated for 10 minutes,
and an all-clear situation never calls the model at all.
"""

import hashlib
import logging
from datetime import datetime, timedelta

from strands import Agent, tool
from strands.models import BedrockModel

from . import config, metrics, store

log = logging.getLogger(__name__)

CACHE_MINUTES = 10
MAX_ACTIONS = 5
ACTION_TYPES = ("deploy_pump", "divert_traffic", "close_underpass", "clear_drain", "monitor")

SYSTEM_PROMPT = """You are the Ops Copilot for Bengaluru ward engineers and traffic police during heavy rain.
You turn live flood-risk data into a short dispatch briefing they can act on in the next hour.

Step 1. MUST call get_dispatch_list.
Step 2. For the top 2-3 spots, SHOULD call get_spot_reports to see what citizens are reporting.
Step 3. Decide at most 5 actions, most urgent first. Use only these action types:
  deploy_pump      - water is standing or will be: send a pump crew
  divert_traffic   - an arterial road or underpass is unsafe: post constables, divert two-wheelers
  close_underpass  - verified knee-deep water at an underpass: close it
  clear_drain      - amber with rain coming: clear inlets before it turns red
  monitor          - risk rising but not yet actionable
Every action needs a one-sentence reason grounded in the data (rain numbers, citizen reports, road importance).
Never invent a spot, a number or a report that the tools did not give you.
Step 4. MUST call submit_briefing exactly once, then stop.
  headline: one line, the single most important thing.
  summary_en: 2-3 short sentences in English for the ward WhatsApp group.
  summary_kn: the same summary in Kannada script, natural and simple."""


class _Run:
    def __init__(self, dispatch: list[dict]):
        self.dispatch = dispatch
        self.result: dict | None = None
        self.tools_used: list[str] = []


_run: _Run | None = None


def dispatch_snapshot() -> list[dict]:
    """Red and amber spots, most urgent first, trimmed to what the agent needs."""
    spots = [h for h in store.list_hotspots() if h.get("risk", {}).get("level") in ("red", "amber")]
    spots.sort(key=lambda h: h.get("priority", 0), reverse=True)
    return [
        {
            "id": h["id"],
            "name": h["name"],
            "kind": h.get("kind", "road"),
            "importance": h.get("importance", 1),
            "level": h["risk"]["level"],
            "score": round(h["risk"].get("score", 0), 2),
            "priority": h.get("priority", 0),
            "drivers": h["risk"].get("drivers", []),
            "verified_reports_recent": h.get("verified_reports_recent", 0),
        }
        for h in spots[:10]
    ]


@tool
def get_dispatch_list() -> dict:
    """Red and amber flood spots right now, ranked by dispatch priority (highest first)."""
    _run.tools_used.append("get_dispatch_list")
    return {"spots": _run.dispatch, "count": len(_run.dispatch)}


@tool
def get_spot_reports(spot_id: str) -> dict:
    """Verified citizen photo reports from the last 3 hours at one spot.

    Args:
        spot_id: The id of a spot from get_dispatch_list.
    """
    _run.tools_used.append(f"get_spot_reports({spot_id})")
    if spot_id not in {s["id"] for s in _run.dispatch}:
        return {"error": f"unknown spot '{spot_id}'. Use an id from get_dispatch_list."}
    reports = [r for r in store.recent_reports(spot_id, hours=3) if r.get("verified")]
    return {
        "count": len(reports),
        "reports": [
            {"minutes_ago": _minutes_ago(r["created_at"]), "depth": r.get("depth"), "reason": r.get("reason")}
            for r in reports[:5]
        ],
    }


@tool
def submit_briefing(headline: str, actions: list[dict], summary_en: str, summary_kn: str) -> str:
    """Submit the final dispatch briefing. Call exactly once.

    Args:
        headline: One line: the single most important thing right now.
        actions: Up to 5 objects, most urgent first, each {"spot_id": str, "action": str, "reason": str}.
                 action is one of deploy_pump, divert_traffic, close_underpass, clear_drain, monitor.
        summary_en: 2-3 short English sentences for the ward WhatsApp group.
        summary_kn: The same summary in Kannada script.
    """
    _run.tools_used.append("submit_briefing")
    known = {s["id"]: s for s in _run.dispatch}
    clean, problems = [], []
    for item in actions[:MAX_ACTIONS]:
        spot_id, action = item.get("spot_id"), item.get("action")
        if spot_id not in known:
            problems.append(f"unknown spot_id '{spot_id}'")
        elif action not in ACTION_TYPES:
            problems.append(f"invalid action '{action}' for {spot_id}")
        else:
            clean.append({
                "spot_id": spot_id,
                "name": known[spot_id]["name"],
                "level": known[spot_id]["level"],
                "action": action,
                "reason": str(item.get("reason", "")).strip()[:240],
            })
    if problems:
        return "Fix these and call submit_briefing again: " + "; ".join(problems)
    _run.result = {
        "headline": headline.strip()[:160],
        "actions": clean,
        "summary_en": summary_en.strip()[:600],
        "summary_kn": summary_kn.strip()[:900],
    }
    return "Briefing recorded. You are done."


def _minutes_ago(iso: str) -> int:
    return int((store.now_utc() - datetime.fromisoformat(iso)).total_seconds() // 60)


def fingerprint(dispatch: list[dict]) -> str:
    """Changes whenever a spot's level or verified-report count changes."""
    key = "|".join(f"{s['id']}:{s['level']}:{s['verified_reports_recent']}" for s in dispatch)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def build_agent() -> Agent:
    model = BedrockModel(
        model_id=config.MODEL_ID,
        region_name=config.BEDROCK_REGION,
        temperature=0.2,
        max_tokens=1500,
    )
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_dispatch_list, get_spot_reports, submit_briefing],
        callback_handler=None,
    )


ALL_CLEAR = {
    "headline": "All clear: no spot is amber or red right now.",
    "actions": [],
    "summary_en": "No waterlogging risk at any tracked spot right now. Neeru re-checks rainfall every 15 minutes.",
    "summary_kn": "ಸದ್ಯಕ್ಕೆ ಯಾವುದೇ ಸ್ಥಳದಲ್ಲಿ ನೀರು ನಿಲ್ಲುವ ಅಪಾಯವಿಲ್ಲ. ನೀರು ಪ್ರತಿ 15 ನಿಮಿಷಕ್ಕೊಮ್ಮೆ ಮಳೆಯನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ.",
}


def get_briefing(force: bool = False, agent_factory=None) -> dict:
    """The current briefing, from cache when the situation has not changed."""
    global _run
    agent_factory = agent_factory or build_agent
    dispatch = dispatch_snapshot()
    now = store.now_utc()

    if not dispatch:
        return {**ALL_CLEAR, "generated_at": now.isoformat(), "cached": False, "tools_used": [], "source": "rule"}

    print_key = fingerprint(dispatch)
    settings = store.get_settings()
    cached = settings.get("briefing")
    if (not force and cached and cached.get("fingerprint") == print_key
            and datetime.fromisoformat(cached["generated_at"]) > now - timedelta(minutes=CACHE_MINUTES)):
        return {**cached, "cached": True}

    _run = _Run(dispatch)
    try:
        with metrics.timer("AgentLatency", Agent="ops_copilot"):
            agent_factory()("Write the dispatch briefing for right now.")
    except Exception:
        log.exception("ops copilot failed")

    if _run.result is None:
        # Fallback that never invents anything: the top priorities, straight from the data.
        result = {
            "headline": f"{dispatch[0]['name']} is the top priority.",
            "actions": [
                {"spot_id": s["id"], "name": s["name"], "level": s["level"],
                 "action": "deploy_pump" if s["level"] == "red" else "clear_drain",
                 "reason": "; ".join(s["drivers"])}
                for s in dispatch[:MAX_ACTIONS]
            ],
            "summary_en": "Automatic briefing (AI unavailable): spots listed in priority order.",
            "summary_kn": "ಸ್ವಯಂಚಾಲಿತ ಪಟ್ಟಿ: ಆದ್ಯತೆಯ ಕ್ರಮದಲ್ಲಿ ಸ್ಥಳಗಳು.",
            "source": "fallback",
        }
    else:
        result = {**_run.result, "source": "agent"}

    result.update({"generated_at": now.isoformat(), "fingerprint": print_key, "tools_used": _run.tools_used})
    store.put_settings({**settings, "briefing": result})
    return {**result, "cached": False}
