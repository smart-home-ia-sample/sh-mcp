from app import registration
from app.registration import TOOL_NAMES, TOOLS


def test_catalog_covers_the_ten_verbs_with_examples_and_tags():
    assert TOOL_NAMES == [t["id"] for t in TOOLS]
    assert set(TOOL_NAMES) == {
        "turn_on", "turn_off", "set_brightness", "set_temperature",
        "open", "close", "lock", "unlock", "arm", "disarm",
    }
    for tool in TOOLS:
        assert tool["examples"] and tool["tags"] and tool["description"]


def test_register_with_bfa_builds_a_service_info_and_calls_through(monkeypatch):
    seen = {}

    def fake_register_with_retry(client, bfa_url, service, *, kind, max_attempts):
        seen.update(bfa_url=bfa_url, kind=kind, max_attempts=max_attempts, service=service)
        return {"status": "registered"}

    monkeypatch.setattr(registration, "register_with_retry", fake_register_with_retry)

    result = registration.register_with_bfa("http://bfa:8000", port=8100, path="/mcp", max_attempts=3)

    assert result == {"status": "registered"}
    assert seen["bfa_url"] == "http://bfa:8000"
    assert seen["kind"] == "mcp"
    assert seen["max_attempts"] == 3
    assert seen["service"].name == "home-mcp"
    assert seen["service"].capabilities == TOOL_NAMES
    assert seen["service"].catalog == TOOLS
