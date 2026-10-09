"""The verifier agent, driven by a fake agent so no Bedrock call is made."""

from neeru import verifier
from tests.conftest import JPEG


class FakeAgent:
    """Stands in for a Strands Agent: calls the tools the way the model would."""

    def __init__(self, verdict: dict | None, use_tools=True):
        self.verdict = verdict
        self.use_tools = use_tools
        self.prompt = None

    def __call__(self, prompt):
        self.prompt = prompt
        if self.use_tools:
            verifier.nearby_reports()
        if self.verdict is not None:
            verifier.submit_verdict(**self.verdict)


GOOD = dict(is_waterlogging=True, depth="tyre_hub", confidence=0.85, is_valid_photo=True,
            reason="Water reaches scooter hubs.", rider_advice="Avoid on a two-wheeler.")


def run(verdict, hotspot={"id": "silk-board", "name": "Silk Board Junction"}, **kwargs):
    agent = FakeAgent(verdict, **kwargs)
    result = verifier.verify(JPEG, "jpeg", 12.917, 77.623, hotspot, "en", agent_factory=lambda lang: agent)
    return result, agent


def test_confident_valid_photo_is_verified(aws):
    result, agent = run(GOOD)
    assert result["verified"] is True
    assert result["depth"] == "tyre_hub"
    assert result["tools_used"] == ["nearby_reports", "submit_verdict"]
    # the photo is passed as an image content block
    assert agent.prompt[1]["image"]["format"] == "jpeg"


def test_low_confidence_is_kept_but_not_verified(aws):
    result, _ = run({**GOOD, "confidence": 0.4})
    assert result["verified"] is False


def test_invalid_photo_never_moves_the_map(aws):
    result, _ = run({**GOOD, "is_valid_photo": False, "confidence": 0.95})
    assert result["verified"] is False
    assert result["depth"] == "none"


def test_bad_depth_is_rejected(aws):
    # the tool answers with an error so a real model would retry; our fake does not
    result, _ = run({**GOOD, "depth": "waist"})
    assert result["verified"] is False
    assert result.get("agent_failed") is True


def test_agent_crash_falls_back_to_unverified(aws):
    def broken_factory(_lang):
        raise RuntimeError("bedrock down")
    result = verifier.verify(JPEG, "jpeg", 12.9, 77.6, None, agent_factory=broken_factory)
    assert result["verified"] is False and result["agent_failed"] is True


def test_dry_road_confirmation_is_verified_but_not_waterlogging(aws):
    result, _ = run({**GOOD, "is_waterlogging": True, "depth": "none"})
    assert result["verified"] is True
    assert result["is_waterlogging"] is False
