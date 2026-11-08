from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vercel_serves_static_frontend_and_proxies_api_to_backend():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["outputDirectory"] == "frontend"
    assert (ROOT / "frontend" / "index.html").is_file()
    rewrites = config.get("rewrites", [])
    api_rewrite = next((item for item in rewrites if item.get("source") == "/api/:path*"), None)
    assert api_rewrite is not None
    assert api_rewrite["destination"].startswith("https://")
    assert api_rewrite["destination"].endswith("/api/:path*")
    # Both REST endpoints and the live-room WebSocket use the same /api namespace.
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    assert "${protocol}//${location.host}/api/live-room/voice" in app_js
    assert "/api/live-room/voice".startswith(api_rewrite["source"].replace(":path*", ""))


def test_vercel_does_not_enable_cdn_caching_for_private_api_responses():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert not any(
        header.get("key", "").lower() == "x-vercel-enable-rewrite-caching"
        for rule in config.get("headers", [])
        for header in rule.get("headers", [])
    )
    assert not any(rule.get("source", "").startswith("/api/") for rule in config.get("headers", []))


def test_render_blueprint_uses_a_persistent_mount_for_case_data():
    render = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "mountPath: /var/data" in render
    assert "- key: BOLKE_DATA_DIR\n        value: /var/data" in render
    assert "sizeGB: 1" in render


def test_render_blueprint_defines_production_auth_and_email_requirements():
    render = (ROOT / "render.yaml").read_text(encoding="utf-8")
    for variable in (
        "BOLKE_AUTH_REQUIRED",
        "BOLKE_ACCOUNTS_ENABLED",
        "BOLKE_EMAIL_VERIFICATION_REQUIRED",
        "BOLKE_PUBLIC_ORIGIN",
        "BOLKE_ALLOWED_ORIGINS",
        "BOLKE_SMTP_HOST",
        "BOLKE_SMTP_PASSWORD",
        "BOLKE_SMTP_FROM",
        "GNANI_API_KEY",
    ):
        assert f"- key: {variable}" in render
