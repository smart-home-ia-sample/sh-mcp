# sh-mcp

Home MCP server: a thin adapter over the BFF. Generic verb tools (`turn_on`, `open`, `lock`, …) + `home://*` resources rebuilt from the BFF snapshot.

Part of the **Smart Home AI** system — architecture, the full `docker compose`
stack and the end-to-end tests live in `sh-infra`.

## Run the tests
```
pip install -r requirements-dev.txt   # needs sh-common from the registry
pytest
```

## Build the image
```
docker build -t sh-mcp .
```
