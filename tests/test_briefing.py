"""Ops Copilot: tool behaviour, validation, caching and fallbacks, with a fake agent."""

import json

from handlers import api
from neeru import briefing, store


def make_red(*ids):
    for spot_id in ids:
        store.update_hotspot(spot_id, {
            "risk": {"level": "red", "score": 1.3, "drivers": ["30 mm rain forecast in the next 3 h"]},
            "priority": 3.9, "verified_reports_recent": 1,
        })


class FakeCopilot:
    """Behaves like the model: reads the list, checks one spot, submits."""

    def __init__(self, actions=None):
        self.calls = 0
        self.actions = actions

    def __call__(self, _prompt):
        self.calls += 1
        spots = briefing.get_dispatch_list()["spots"]
        briefing.get_spot_reports(spots[0]["id"])
        actions = self.actions or [{"spot_id": spots[0]["id"], "action": "deploy_pump", "reason": "30 mm coming."}]
        briefing.submit_briefing("Send a pump to K.R. Circle now.", actions, "Pump to K.R. Circle.", "ಕೆ.ಆರ್. ವೃತ್ತಕ್ಕೆ ಪಂಪ್.")


def test_all_clear_never_calls_the_model(aws):
    def explode():
        raise AssertionError("model should not be called")
    result = briefing.get_briefing(agent_factory=explode)
    assert result["actions"] == [] and result["source"] == "rule"


def test_agent_briefing_is_returned_and_cached(aws):
    make_red("kr-circle")
    agent = FakeCopilot()
    first = briefing.get_briefing(agent_factory=lambda: agent)
    assert first["source"] == "agent" and first["cached"] is False
    assert first["actions"][0]["name"] == "K.R. Circle Underpass"
    assert first["tools_used"] == ["get_dispatch_list", "get_spot_reports(kr-circle)", "submit_briefing"]

    second = briefing.get_briefing(agent_factory=lambda: agent)
    assert second["cached"] is True and agent.calls == 1

    briefing.get_briefing(force=True, agent_factory=lambda: agent)
    assert agent.calls == 2


def test_cache_is_invalidated_when_the_situation_changes(aws):
    make_red("kr-circle")
    agent = FakeCopilot()
    briefing.get_briefing(agent_factory=lambda: agent)
    make_red("silk-board")
    briefing.get_briefing(agent_factory=lambda: agent)
    assert agent.calls == 2


def test_invented_spots_and_actions_are_rejected(aws):
    make_red("kr-circle")
    briefing._run = briefing._Run(briefing.dispatch_snapshot())
    message = briefing.submit_briefing("x", [{"spot_id": "mg-road", "action": "deploy_pump", "reason": ""}], "a", "b")
    assert "unknown spot_id" in message and briefing._run.result is None
    message = briefing.submit_briefing("x", [{"spot_id": "kr-circle", "action": "call_army", "reason": ""}], "a", "b")
    assert "invalid action" in message


def test_agent_failure_falls_back_to_the_data(aws):
    make_red("kr-circle", "okalipuram")

    def broken():
        raise RuntimeError("bedrock down")
    result = briefing.get_briefing(agent_factory=broken)
    assert result["source"] == "fallback"
    assert {a["spot_id"] for a in result["actions"]} == {"kr-circle", "okalipuram"}


def test_briefing_endpoint_only_admins_can_force(aws, monkeypatch):
    seen = []
    monkeypatch.setattr(briefing, "get_briefing", lambda force=False: seen.append(force) or {"ok": True})
    body = json.dumps({"force": True})
    api.handler({"routeKey": "POST /ops/briefing", "headers": {}, "body": body}, None)
    api.handler({"routeKey": "POST /ops/briefing", "headers": {"x-admin-token": "admin-token-1234567890"}, "body": body}, None)
    assert seen == [False, True]
