"""The real bff_client against an httpx.MockTransport (no BFF, no self-login)."""

import httpx
import pytest

from app import bff_client
from app.bff_client import BffUnavailableError, DeviceCommandError

HOMES = [{"id": "home-1", "isDefault": True}, {"id": "home-2", "isDefault": False}]
ROOMS = [{"slug": "sala", "name": "Sala"}]
DEVICES = [
    {"id": "uuid-lamp", "slug": "living_room_light", "nickname": "Luz", "type": "light", "roomSlug": "sala"},
    {"id": "uuid-door", "slug": "front_door", "nickname": "Porta", "type": "door", "roomSlug": "sala"},
]


def _install(monkeypatch, handler):
    """Route every bff_client HTTP call through `handler`, with no auth header."""
    monkeypatch.setattr(bff_client, "_headers", lambda: {})
    monkeypatch.setattr(
        bff_client,
        "_client",
        lambda: httpx.Client(base_url=bff_client.BFF_URL, transport=httpx.MockTransport(handler), timeout=5.0),
    )


def _default_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/homes":
        return httpx.Response(200, json=HOMES)
    if path == "/api/homes/home-1/rooms":
        return httpx.Response(200, json=ROOMS)
    if path == "/api/homes/home-1/devices":
        return httpx.Response(200, json=DEVICES)
    if path == "/api/home-status/snapshot":
        return httpx.Response(200, json={"simulatorOnline": True, "rooms": [], "rollups": {}, "events": []})
    if path == "/api/devices/uuid-lamp/command":
        return httpx.Response(200, json={"state": {"on": True}})
    if path == "/api/devices/uuid-door/command":
        return httpx.Response(409, json={"detail": "device not provisioned yet"})
    return httpx.Response(404)


def test_topology_builds_the_by_slug_index(monkeypatch):
    _install(monkeypatch, _default_handler)

    topo = bff_client.topology()

    assert topo["homeId"] == "home-1"  # the default home
    assert set(topo["by_slug"]) == {"living_room_light", "front_door"}
    assert topo["by_slug"]["front_door"]["type"] == "door"


def test_topology_raises_when_the_user_has_no_home(monkeypatch):
    _install(monkeypatch, lambda r: httpx.Response(200, json=[]))
    with pytest.raises(BffUnavailableError):
        bff_client.topology()


def test_topology_wraps_transport_errors(monkeypatch):
    def boom(request):
        raise httpx.ConnectError("refused", request=request)

    _install(monkeypatch, boom)
    with pytest.raises(BffUnavailableError):
        bff_client.topology()


def test_snapshot_returns_the_bff_payload(monkeypatch):
    _install(monkeypatch, _default_handler)
    assert bff_client.snapshot()["simulatorOnline"] is True


def test_command_resolves_the_slug_and_returns_the_confirmed_state(monkeypatch):
    _install(monkeypatch, _default_handler)
    assert bff_client.command("living_room_light", "turn_on") == {"on": True}


def test_command_on_an_unknown_slug_is_a_device_command_error(monkeypatch):
    _install(monkeypatch, _default_handler)
    with pytest.raises(DeviceCommandError, match="does not exist"):
        bff_client.command("no_such_device", "turn_on")


def test_command_maps_409_to_a_device_command_error(monkeypatch):
    _install(monkeypatch, _default_handler)
    with pytest.raises(DeviceCommandError, match="not provisioned"):
        bff_client.command("front_door", "lock")


def test_command_maps_503_to_device_did_not_respond(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/devices/uuid-lamp/command":
            return httpx.Response(503, json={})
        return _default_handler(request)

    _install(monkeypatch, handler)
    with pytest.raises(DeviceCommandError, match="did not respond"):
        bff_client.command("living_room_light", "turn_on")


def test_command_passes_a_numeric_value_through(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/devices/uuid-lamp/command":
            captured["body"] = request.content.decode()
            return httpx.Response(200, json={"state": {"brightness": 30}})
        return _default_handler(request)

    _install(monkeypatch, handler)
    assert bff_client.command("living_room_light", "set_brightness", 30) == {"brightness": 30}
    assert '"value": 30' in captured["body"] or '"value":30' in captured["body"]
