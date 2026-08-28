import asyncio
import json

from app import server

VERBS = {
    "turn_on", "turn_off", "set_brightness", "set_temperature",
    "open", "close", "lock", "unlock", "arm", "disarm",
}


def test_mcp_exposes_exactly_the_ten_generic_verbs():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == VERBS


def test_every_tool_wrapper_delegates_to_the_tool_module(monkeypatch):
    calls = []
    for name in ("turn_on", "turn_off", "open_", "close", "lock", "unlock", "arm", "disarm"):
        monkeypatch.setattr(server.tool_defs, name, lambda device_id, _n=name: {"verb": _n, "id": device_id})
    for name in ("set_brightness", "set_temperature"):
        monkeypatch.setattr(server.tool_defs, name, lambda device_id, value, _n=name: {"verb": _n, "id": device_id, "value": value})

    calls.append(server.turn_on("d"))
    calls.append(server.turn_off("d"))
    calls.append(server.open_device("d"))
    calls.append(server.close("d"))
    calls.append(server.lock("d"))
    calls.append(server.unlock("d"))
    calls.append(server.arm("d"))
    calls.append(server.disarm("d"))
    calls.append(server.set_brightness("d", 40))
    calls.append(server.set_temperature("d", 22.5))

    assert {c["verb"] for c in calls} == {
        "turn_on", "turn_off", "open_", "close", "lock", "unlock", "arm", "disarm",
        "set_brightness", "set_temperature",
    }
    assert calls[-1] == {"verb": "set_temperature", "id": "d", "value": 22.5}


def test_health_and_ready_routes():
    for route in (server.health, server.ready):
        resp = asyncio.run(route(None))
        assert resp.status_code == 200
        assert json.loads(resp.body)["status"] in ("healthy", "ready")


def test_list_tools_route_merges_the_catalog_docs():
    resp = asyncio.run(server.list_tools(None))
    payload = json.loads(resp.body)["tools"]

    assert {t["name"] for t in payload} == VERBS
    turn_on = next(t for t in payload if t["name"] == "turn_on")
    assert turn_on["annotations"]["examples"]  # pulled from tools_catalog.TOOLS
    assert isinstance(turn_on["input_schema"], dict)


def test_resource_helpers_are_wired(monkeypatch):
    monkeypatch.setattr(server.resource_defs, "rooms", lambda: [{"slug": "sala"}])
    monkeypatch.setattr(server.resource_defs, "security", lambda: {"alarmArmed": False})
    assert server.home_rooms() == [{"slug": "sala"}]
    assert server.home_security() == {"alarmArmed": False}


def test_tools_route_is_backed_by_the_static_catalog():
    # /tools is what the BFA pulls into its catalog — it must expose the same
    # verbs the tool wrappers register.
    from app.tools_catalog import TOOLS

    assert {t["id"] for t in TOOLS} == VERBS
