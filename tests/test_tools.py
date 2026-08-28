"""Tools now delegate to the BFF. We fake the BFF adapter (`bff_client`) with a
tiny in-memory house so the wrapper logic — action mapping, error translation,
slug-as-id — is exercised without a running BFF."""

import pytest

from app import bff_client, resources, tools
from app.bff_client import BffUnavailableError, DeviceCommandError

# slug -> (type, mutable state)
_HOUSE = {
    "living_room_light": ("light", {"on": True, "brightness": 80}),
    "bedroom_ac": ("ac", {"on": False, "temperature": 24}),
    "front_door": ("door", {"locked": False, "open": False}),
    "alarm": ("alarm", {"armed": False}),
    "living_room_curtain": ("curtain", {"open": True}),
    "kitchen_refrigerator": ("refrigerator", {"on": True}),
}

_ACTION_EFFECT = {
    "turn_on": lambda s: s.update(on=True),
    "turn_off": lambda s: s.update(on=False),
    "set_brightness": lambda s, v: s.update(brightness=int(v)),
    "set_temperature": lambda s, v: s.update(temperature=v),
    "open": lambda s: s.update(open=True),
    "close": lambda s: s.update(open=False),
    "lock": lambda s: s.update(locked=True),
    "unlock": lambda s: s.update(locked=False),
    "arm": lambda s: s.update(armed=True),
    "disarm": lambda s: s.update(armed=False),
}

_VALID_TYPES = {
    "turn_on": {"light", "ac", "tv", "coffee_maker", "refrigerator"},
    "turn_off": {"light", "ac", "tv", "coffee_maker", "refrigerator"},
    "set_brightness": {"light", "dimmable_light"},
    "set_temperature": {"ac"},
    "open": {"curtain", "window"},
    "close": {"curtain", "window"},
    "lock": {"door"},
    "unlock": {"door"},
    "arm": {"alarm"},
    "disarm": {"alarm"},
}


@pytest.fixture(autouse=True)
def fake_bff(monkeypatch):
    house = {k: (t, dict(s)) for k, (t, s) in _HOUSE.items()}

    def fake_command(slug, action, value=None):
        if slug not in house:
            raise DeviceCommandError(f"device '{slug}' does not exist")
        dtype, state = house[slug]
        if dtype not in _VALID_TYPES[action]:
            raise DeviceCommandError(f"action '{action}' is not valid for a {slug}")
        effect = _ACTION_EFFECT[action]
        effect(state, value) if value is not None else effect(state)
        return {"id": "uuid-of-" + slug, "type": dtype, **state}

    monkeypatch.setattr(bff_client, "command", fake_command)
    return house


def test_turn_on_and_off():
    assert tools.turn_off("living_room_light")["state"] == {
        "id": "living_room_light", "type": "light", "on": False, "brightness": 80,
    }
    assert tools.turn_on("living_room_light")["state"]["on"] is True


def test_state_id_is_the_slug_not_the_bff_uuid():
    assert tools.turn_off("living_room_light")["state"]["id"] == "living_room_light"


def test_one_verb_covers_every_switchable_type():
    # the whole point of the redesign: no turn_light_on / turn_ac_on split
    assert tools.turn_on("bedroom_ac")["state"]["on"] is True
    assert tools.turn_off("kitchen_refrigerator")["state"]["on"] is False


def test_set_brightness_valid_and_invalid():
    assert tools.set_brightness("living_room_light", 50)["state"]["brightness"] == 50
    invalid = tools.set_brightness("living_room_light", 150)
    assert invalid["ok"] is False and "brightness" in invalid["error"]


def test_set_temperature():
    assert tools.set_temperature("bedroom_ac", 19)["state"]["temperature"] == 19


def test_lock_and_unlock():
    assert tools.lock("front_door")["state"]["locked"] is True
    assert tools.unlock("front_door")["state"]["locked"] is False


def test_arm_and_disarm_take_the_alarm_device_id():
    assert tools.arm("alarm")["state"]["armed"] is True
    assert tools.disarm("alarm")["state"]["armed"] is False


def test_open_and_close():
    assert tools.close("living_room_curtain")["state"]["open"] is False
    assert tools.open_("living_room_curtain")["state"]["open"] is True


def test_unknown_device_is_an_explicit_error():
    result = tools.turn_on("does_not_exist")
    assert result["ok"] is False and "does_not_exist" in result["error"]


def test_wrong_device_type_is_an_explicit_error():
    result = tools.lock("living_room_light")
    assert result["ok"] is False and "living_room_light" in result["error"]


def test_bff_unavailable_is_an_explicit_error(monkeypatch):
    def boom(*_a, **_k):
        raise BffUnavailableError("BFF command failed: connect error")

    monkeypatch.setattr(bff_client, "command", boom)
    result = tools.turn_off("living_room_light")
    assert result["ok"] is False and "BFF" in result["error"]


def test_repeated_call_is_idempotent():
    first = tools.turn_off("living_room_light")
    second = tools.turn_off("living_room_light")
    assert first["ok"] and second["ok"]
    assert second["state"]["on"] is False


# ---- resource shapes rebuilt from the snapshot ---------------------------------

_SNAPSHOT = {
    "simulatorOnline": True,
    "rooms": [
        {"slug": "living_room", "name": "Sala", "devices": [
            {"deviceId": "u1", "slug": "living_room_light", "nickname": "Luz da sala", "type": "light",
             "capabilities": {"traits": [
                 {"trait": "on_off", "commands": ["turn_on", "turn_off"], "state": ["on"]}]},
             "state": {"on": True, "brightness": 80}},
            {"deviceId": "u2", "slug": "motion_sensor", "nickname": "Sensor", "type": "motion_sensor",
             "capabilities": {"traits": [{"trait": "occupancy", "commands": [], "state": ["active"]}]},
             "state": {"active": False}},
        ]},
        {"slug": "bedroom", "name": "Quarto", "devices": [
            {"deviceId": "u3", "slug": "bedroom_ac", "nickname": "AC", "type": "ac",
             "state": {"on": True, "temperature": 21}},
        ]},
        {"slug": "entrance", "name": "Entrada", "devices": [
            {"deviceId": "u4", "slug": "front_door", "nickname": "Porta", "type": "door",
             "state": {"locked": True, "open": False}},
        ]},
        {"slug": "whole_home", "name": "Casa toda", "devices": [
            {"deviceId": "u5", "slug": "alarm", "nickname": "Alarme", "type": "alarm",
             "state": {"armed": False}},
        ]},
    ],
    "rollups": {"alarmArmed": False, "allDoorsLocked": True, "openDoors": 0, "totalWatts": 1510, "activeDevices": 2},
    "events": [
        {"deviceId": "u1", "slug": "living_room_light", "nickname": "Luz da sala", "type": "light",
         "state": {"on": False}, "at": 1700000000000},
    ],
}


@pytest.fixture(autouse=True)
def fake_snapshot(monkeypatch):
    monkeypatch.setattr(bff_client, "snapshot", lambda: _SNAPSHOT)


def test_devices_resource_uses_slug_ids():
    ids = {d["id"] for d in resources.devices()}
    assert "living_room_light" in ids and "bedroom_ac" in ids


def test_devices_resource_carries_the_allowed_actions():
    by_id = {d["id"]: d for d in resources.devices()}
    assert by_id["living_room_light"]["actions"] == ["turn_on", "turn_off"]
    # a read-only device (occupancy trait, no commands) exposes no actions key
    assert "actions" not in by_id["motion_sensor"]


def test_security_resource_shape():
    sec = resources.security()
    assert sec["doors"]["front_door"] == {"locked": True, "open": False}
    assert sec["alarm_armed"] is False
    assert sec["presence_detected"] is False


def test_environment_resource_shape():
    env = resources.environment()
    assert env["living_room"]["light"] == {"on": True, "brightness": 80}
    assert env["bedroom"]["ac"] == {"on": True, "temperature": 21}


def test_energy_resource_computes_watts():
    energy = resources.energy()
    assert energy["total_watts"] == 1510  # light 10 + ac 1500
    assert energy["top_consumers"][0]["device_id"] == "bedroom_ac"


def test_events_resource_shape():
    ev = resources.events()
    assert ev[0]["device_id"] == "living_room_light"
    assert ev[0]["action"] == "device_off"
