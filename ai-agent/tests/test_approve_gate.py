import pytest

from settings import auto_outreach_enabled, approve_key_ok


def _route_after_research(state: dict, enabled: bool) -> str:
    if enabled and state.get("researched_candidates"):
        return "outreach_vendors"
    return "generate_reference"


def test_auto_outreach_defaults_false(monkeypatch):
    monkeypatch.delenv("AUTO_OUTREACH", raising=False)
    assert auto_outreach_enabled() is False


@pytest.mark.parametrize("value", ["false", "False", "0", "no", ""])
def test_auto_outreach_falsey(monkeypatch, value):
    monkeypatch.setenv("AUTO_OUTREACH", value)
    assert auto_outreach_enabled() is False


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
def test_auto_outreach_truthy(monkeypatch, value):
    monkeypatch.setenv("AUTO_OUTREACH", value)
    assert auto_outreach_enabled() is True


def test_places_path_skips_outreach_when_gated():
    assert _route_after_research({"researched_candidates": [{"phone": "+1"}]}, False) == "generate_reference"


def test_places_path_outreach_when_auto():
    assert _route_after_research({"researched_candidates": [{"phone": "+1"}]}, True) == "outreach_vendors"


def test_approve_key_rejects_empty_secret(monkeypatch):
    monkeypatch.setenv("APPROVE_SECRET", "")
    assert approve_key_ok("anything") is False


def test_approve_key_matches(monkeypatch):
    monkeypatch.setenv("APPROVE_SECRET", "s3cret")
    assert approve_key_ok("s3cret") is True
    assert approve_key_ok("wrong") is False
    assert approve_key_ok(None) is False
