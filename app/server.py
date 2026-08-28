import os
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from app import prompts as prompt_defs
from app import resources as resource_defs
from app import tools as tool_defs
from app.tools_catalog import TOOLS

try:
    from mcp.server.fastmcp import FastMCP as MCPServerClass
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer as MCPServerClass

MCP_PORT = int(os.environ.get("MCP_PORT", "8100"))
MCP_PATH = os.environ.get("MCP_PATH", "/mcp")

# No self-registration: the BFA pulls `GET /tools` into its catalog (spec/13).
mcp = MCPServerClass(name="home-mcp", version="0.1.0")


# ---- tools: one generic verb per semantic action, thin over the BFF ---------
# The device_id disambiguates; the BFF validates the verb against the device's
# announced capability descriptor.


@mcp.tool(structured_output=True)
def turn_on(device_id: str) -> dict[str, Any]:
    return tool_defs.turn_on(device_id)


@mcp.tool(structured_output=True)
def turn_off(device_id: str) -> dict[str, Any]:
    return tool_defs.turn_off(device_id)


@mcp.tool(structured_output=True)
def set_brightness(device_id: str, value: int) -> dict[str, Any]:
    return tool_defs.set_brightness(device_id, value)


@mcp.tool(structured_output=True)
def set_temperature(device_id: str, value: float) -> dict[str, Any]:
    return tool_defs.set_temperature(device_id, value)


@mcp.tool(structured_output=True, name="open")
def open_device(device_id: str) -> dict[str, Any]:
    return tool_defs.open_(device_id)


@mcp.tool(structured_output=True)
def close(device_id: str) -> dict[str, Any]:
    return tool_defs.close(device_id)


@mcp.tool(structured_output=True)
def lock(device_id: str) -> dict[str, Any]:
    return tool_defs.lock(device_id)


@mcp.tool(structured_output=True)
def unlock(device_id: str) -> dict[str, Any]:
    return tool_defs.unlock(device_id)


@mcp.tool(structured_output=True)
def arm(device_id: str) -> dict[str, Any]:
    return tool_defs.arm(device_id)


@mcp.tool(structured_output=True)
def disarm(device_id: str) -> dict[str, Any]:
    return tool_defs.disarm(device_id)


# ---- resources: rebuilt from the BFF home-status snapshot ----------------


@mcp.resource("home://rooms", mime_type="application/json")
def home_rooms() -> list[dict]:
    return resource_defs.rooms()


@mcp.resource("home://devices", mime_type="application/json")
def home_devices() -> list[dict]:
    return resource_defs.devices()


@mcp.resource("home://security", mime_type="application/json")
def home_security() -> dict:
    return resource_defs.security()


@mcp.resource("home://environment", mime_type="application/json")
def home_environment() -> dict:
    return resource_defs.environment()


@mcp.resource("home://energy", mime_type="application/json")
def home_energy() -> dict:
    return resource_defs.energy()


@mcp.resource("home://events", mime_type="application/json")
def home_events() -> list[dict]:
    return resource_defs.events()


@mcp.prompt()
def leave_home() -> str:
    return prompt_defs.leave_home()


@mcp.prompt()
def bedtime() -> str:
    return prompt_defs.bedtime()


@mcp.prompt()
def energy_optimization() -> str:
    return prompt_defs.energy_optimization()


@mcp.prompt()
def home_status() -> str:
    return prompt_defs.home_status()


# ---- custom routes ------------------------------------------------------------

_TOOL_DOCS = {tool["id"]: tool for tool in TOOLS}


@mcp.custom_route("/tools", methods=["GET"])
async def list_tools(request: Request) -> JSONResponse:
    tools = await mcp.list_tools()
    payload = []
    for tool in tools:
        doc = _TOOL_DOCS.get(tool.name, {})
        input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "parameters", None) or {}
        payload.append(
            {
                "name": tool.name,
                "description": tool.description or doc.get("description", ""),
                "input_schema": input_schema,
                "annotations": {"tags": doc.get("tags", []), "examples": doc.get("examples", [])},
            }
        )
    return JSONResponse({"tools": payload})


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})


@mcp.custom_route("/ready", methods=["GET"])
async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})
