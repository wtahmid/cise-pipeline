from demo_app.main import handle


def test_healthz_route():
    assert handle("/healthz") == ("200", '{"status":"ok"}')


def test_version_route():
    status, body = handle("/version")
    assert status == "200"
    assert '"version":"0.1.0"' in body


def test_unknown_route_returns_404():
    assert handle("/nope") == ("404", "not found")


def test_routes_are_exact():
    # Regression guard: no wildcard/fallback should shadow a known path.
    for path in ("/healthz", "/version"):
        status, _ = handle(path)
        assert status == "200", f"{path} should resolve"
