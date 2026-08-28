"""`home://*` resources, rebuilt from the BFF's home-status snapshot into the
legacy shapes the agents parse. The MCP holds no state of its own."""

from app import bff_client

WATTS_WHEN_ON = {
    "light": 10,
    "dimmable_light": 10,
    "tv": 120,
    "ac": 1500,
    "coffee_maker": 900,
    "refrigerator": 150,
}


def _iter_devices(snap: dict):
    for room in snap.get("rooms", []):
        for d in room.get("devices", []):
            yield room["slug"], d["slug"], d["type"], (d.get("state") or {})


def _actions_of(device: dict) -> list[str]:
    """Flatten the announced capability descriptor into the list of verbs this
    device accepts, so the orchestrator can validate an action per device."""
    caps = device.get("capabilities") or {}
    return [cmd for trait in caps.get("traits", []) for cmd in (trait.get("commands") or [])]


def devices() -> list[dict]:
    snap = bff_client.snapshot()
    out = []
    for room in snap.get("rooms", []):
        for d in room.get("devices", []):
            state = d.get("state") or {}
            entry = {"id": d["slug"], "room": room["slug"], "type": d["type"]}
            for key in ("on", "brightness", "temperature", "open", "locked", "armed", "active"):
                if key in state:
                    entry[key] = state[key]
            actions = _actions_of(d)
            if actions:
                entry["actions"] = actions
            out.append(entry)
    return out


def rooms() -> list[dict]:
    snap = bff_client.snapshot()
    return [
        {"room": room["slug"], "devices": [d["slug"] for d in room.get("devices", [])]}
        for room in snap.get("rooms", [])
    ]


def security() -> dict:
    snap = bff_client.snapshot()
    doors, windows = {}, {}
    alarm_armed = False
    presence = False
    for _room, slug, dtype, state in _iter_devices(snap):
        if dtype == "door":
            doors[slug] = {"locked": bool(state.get("locked")), "open": bool(state.get("open"))}
        elif dtype == "window":
            windows[slug] = {"open": bool(state.get("open"))}
        elif dtype == "alarm":
            alarm_armed = bool(state.get("armed"))
        elif dtype == "motion_sensor":
            presence = bool(state.get("active"))
    return {"doors": doors, "windows": windows, "alarm_armed": alarm_armed, "presence_detected": presence}


def environment() -> dict:
    snap = bff_client.snapshot()
    result: dict[str, dict] = {}
    for room_slug, _slug, dtype, state in _iter_devices(snap):
        room = result.setdefault(room_slug, {})
        if dtype in ("light", "dimmable_light"):
            room["light"] = {"on": bool(state.get("on")), "brightness": state.get("brightness", 0)}
        elif dtype == "ac":
            room["ac"] = {"on": bool(state.get("on")), "temperature": state.get("temperature")}
        elif dtype == "curtain":
            room["curtain"] = {"open": bool(state.get("open"))}
    return {room: env for room, env in result.items() if env}


def energy() -> dict:
    snap = bff_client.snapshot()
    consumers = []
    total = 0.0
    on_by_slug = {}
    for _room, slug, dtype, state in _iter_devices(snap):
        on_by_slug[slug] = state
        watts = WATTS_WHEN_ON.get(dtype)
        if watts is None or not state.get("on"):
            continue
        total += watts
        consumers.append({"device_id": slug, "type": dtype, "watts": watts})

    consumers.sort(key=lambda c: c["watts"], reverse=True)

    recommendations = []
    if on_by_slug.get("kitchen_coffee_maker", {}).get("on"):
        recommendations.append("kitchen_coffee_maker está ligada; desligue se não estiver em uso.")
    ac = on_by_slug.get("bedroom_ac", {})
    window = on_by_slug.get("bedroom_window", {})
    if ac.get("on") and window.get("open"):
        recommendations.append("bedroom_ac está ligado com a janela aberta; feche a janela para economizar energia.")

    return {"total_watts": total, "top_consumers": consumers, "recommendations": recommendations}


def _event_action(state: dict) -> str:
    if "on" in state:
        return "device_on" if state["on"] else "device_off"
    if "open" in state:
        return "opened" if state["open"] else "closed"
    if "locked" in state:
        return "locked" if state["locked"] else "unlocked"
    if "armed" in state:
        return "armed" if state["armed"] else "disarmed"
    if "active" in state:
        return "motion_detected" if state["active"] else "motion_cleared"
    return "state_changed"


def events(limit: int = 20) -> list[dict]:
    snap = bff_client.snapshot()
    out = []
    for e in snap.get("events", [])[:limit]:
        state = e.get("state") or {}
        out.append(
            {
                "action": _event_action(state),
                "device_id": e.get("slug") or e.get("nickname"),
                "resulting_state": state,
                "timestamp": e.get("at", 0) / 1000.0,
            }
        )
    return out
