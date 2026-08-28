from app import main


def test_main_builds_the_streamable_http_app_with_auth_middleware_and_serves(monkeypatch):
    built = {}

    class FakeApp:
        def add_middleware(self, mw, *a, **k):
            built.setdefault("middleware", []).append(mw)

    def fake_app(**kw):
        built["kw"] = kw
        return FakeApp()

    monkeypatch.setattr(main.mcp, "streamable_http_app", fake_app)
    monkeypatch.setattr(main.uvicorn, "run", lambda app, **kw: built.update(run=kw))

    main.main()

    assert built["kw"]["host"] == "0.0.0.0"
    assert built["kw"]["transport_security"].enable_dns_rebinding_protection is False
    assert main.AuthTokenMiddleware in built["middleware"]
    assert built["run"]["port"] == main.MCP_PORT
