"""Generic verb tools — thin wrappers over the BFF's device-command endpoint.

There is one tool per semantic verb (not per device type): the `device_id`
disambiguates and the BFF validates the verb against the device's announced
capability descriptor. Each returns the legacy `{"ok": bool, "state"|"error"}`
shape the agents and the orchestrator's `EXPECTED_EFFECTS` expect; `state["id"]`
is the device slug (not the BFF UUID)."""

from app import bff_client
from app.bff_client import BffUnavailableError, DeviceCommandError


def _run(slug: str, action: str, value: float | None = None) -> dict:
    try:
        state = bff_client.command(slug, action, value)
        state["id"] = slug  # agents/orchestrator address devices by slug, not the BFF UUID
        return {"ok": True, "state": state}
    except (DeviceCommandError, BffUnavailableError) as exc:
        return {"ok": False, "error": str(exc)}


def turn_on(device_id: str) -> dict:
    return _run(device_id, "turn_on")


def turn_off(device_id: str) -> dict:
    return _run(device_id, "turn_off")


def set_brightness(device_id: str, value: int) -> dict:
    if not 0 <= value <= 100:
        return {"ok": False, "error": f"brightness must be between 0 and 100, got {value}"}
    return _run(device_id, "set_brightness", value)


def set_temperature(device_id: str, value: float) -> dict:
    return _run(device_id, "set_temperature", value)


# `open` shadows the builtin — deliberate; this module does no file I/O. The MCP
# tool is registered as "open" / "close".
def open_(device_id: str) -> dict:
    return _run(device_id, "open")


def close(device_id: str) -> dict:
    return _run(device_id, "close")


def lock(device_id: str) -> dict:
    return _run(device_id, "lock")


def unlock(device_id: str) -> dict:
    return _run(device_id, "unlock")


def arm(device_id: str) -> dict:
    return _run(device_id, "arm")


def disarm(device_id: str) -> dict:
    return _run(device_id, "disarm")
