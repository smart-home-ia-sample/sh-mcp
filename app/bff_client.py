"""The Home MCP is a thin adapter over the BFF. It no longer holds device state:
topology comes from the BFF's CRUD API, live state from the BFF's home-status
snapshot, and mutations go through the BFF's device-command endpoint (which
publishes MQTT and blocks on the echo).

Auth: the end user's JWT is forwarded from the calling agent via the
`Authorization` header (lifted into a contextvar by AuthTokenMiddleware). Entry
points that carry no token (service startup, /converse) fall back to a demo-user
self-login."""

import os

import httpx

from smart_home_common import ServiceLogin, bearer_header, current_token

BFF_URL = os.environ.get("BFF_URL", "http://bff:8080").rstrip("/")

_service_login = ServiceLogin(
    BFF_URL,
    os.environ.get("DEMO_USER", "demo"),
    os.environ.get("DEMO_PASS", "demo"),
)


class BffUnavailableError(Exception):
    pass


class DeviceCommandError(Exception):
    """A command the BFF rejected on domain grounds (unknown device, wrong
    action for the type, device didn't respond)."""


def _headers() -> dict[str, str]:
    token = current_token() or _service_login.token()
    return bearer_header(token)


def _client() -> httpx.Client:
    return httpx.Client(base_url=BFF_URL, headers=_headers(), timeout=10.0)


def _default_home_id(client: httpx.Client) -> str:
    homes = client.get("/api/homes").raise_for_status().json()
    if not homes:
        raise BffUnavailableError("no home for the current user")
    default = next((h for h in homes if h.get("isDefault")), homes[0])
    return default["id"]


def topology() -> dict:
    """{'homeId', 'rooms': [...], 'devices': [{id, slug, nickname, type, roomSlug}],
    'by_slug': {slug: device}}"""
    try:
        with _client() as client:
            home_id = _default_home_id(client)
            rooms = client.get(f"/api/homes/{home_id}/rooms").raise_for_status().json()
            devices = client.get(f"/api/homes/{home_id}/devices").raise_for_status().json()
    except httpx.HTTPError as exc:
        raise BffUnavailableError(f"BFF topology unavailable: {exc}") from exc

    return {
        "homeId": home_id,
        "rooms": rooms,
        "devices": devices,
        "by_slug": {d["slug"]: d for d in devices},
    }


def snapshot() -> dict:
    """The BFF's home-status snapshot: {simulatorOnline, rooms, rollups, events}."""
    try:
        with _client() as client:
            return client.get("/api/home-status/snapshot").raise_for_status().json()
    except httpx.HTTPError as exc:
        raise BffUnavailableError(f"BFF home-status unavailable: {exc}") from exc


def command(slug: str, action: str, value: float | None = None) -> dict:
    """Resolve the slug to the BFF device id and run a semantic command.
    Returns the confirmed device state dict."""
    try:
        with _client() as client:
            device = topology()["by_slug"].get(slug)
            if device is None:
                raise DeviceCommandError(f"device '{slug}' does not exist")
            body: dict = {"action": action}
            if value is not None:
                body["value"] = value
            resp = client.post(f"/api/devices/{device['id']}/command", json=body)
            if resp.status_code == 400:
                raise DeviceCommandError(resp.json().get("detail", "invalid command for this device"))
            if resp.status_code == 409:
                raise DeviceCommandError(resp.json().get("detail", "device not provisioned yet"))
            if resp.status_code in (503, 504):
                raise DeviceCommandError("device did not respond")
            resp.raise_for_status()
            return resp.json()["state"]
    except httpx.HTTPError as exc:
        raise BffUnavailableError(f"BFF command failed: {exc}") from exc
