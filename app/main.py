import os

import uvicorn
from mcp.server.transport_security import TransportSecuritySettings

from app.server import MCP_PATH, MCP_PORT, mcp
from smart_home_common import AuthTokenMiddleware, configure_logging

configure_logging(service="home-mcp", level=os.environ.get("LOG_LEVEL", "INFO"))


def main() -> None:
    # Agents reach us at the BFA-resolved endpoint (a container IP:port), so the
    # streamable-http transport's DNS-rebinding host check must not reject it.
    app = mcp.streamable_http_app(
        streamable_http_path=MCP_PATH,
        host="0.0.0.0",
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    # Lift the caller's JWT (forwarded from the agent) into a contextvar so the
    # BFF adapter forwards it on to the BFF.
    app.add_middleware(AuthTokenMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
