import os

# app.server / app.main read these at import time; set them before collection so
# the modules can be imported in tests without a running BFA / BFF.
os.environ.setdefault("BFA_URL", "http://bfa.test:8000")
os.environ.setdefault("BFF_URL", "http://bff.test:8080")
os.environ.setdefault("DEMO_USER", "demo")
os.environ.setdefault("DEMO_PASS", "demo")
os.environ.setdefault("MCP_PORT", "8100")
