"""The proxy contract: what crosses from bundled pages to the
payments service, and how responses are adapted back to what the
pages understand (the documented compatibility shim). The Qt
handler parses/serializes JSON around these pure functions."""

from __future__ import annotations

from hackproof_app import proxy_logic

PAGE_CERT_BODY = {
    "email": "student@example.com",
    "certificate_code": "CERT-1",
    "payload": {
        "integrity": {"version": 1, "verdict": "clean", "events": 0},
        "fullName": "A Student",
        "scorePct": 95,
    },
}


def test_is_api_path():
    assert proxy_logic.is_api_path("/api")
    assert proxy_logic.is_api_path("/api/orders")
    assert proxy_logic.is_api_path("/api/orders/hp_1")
    assert not proxy_logic.is_api_path("/index.html")
    assert not proxy_logic.is_api_path("/apiary/x")


def test_proxy_target_building():
    assert proxy_logic.proxy_target(
        "https://svc.example/", "/api/orders", "a=1"
    ) == "https://svc.example/api/orders?a=1"
    assert proxy_logic.proxy_target(
        "https://svc.example", "/api/orders", ""
    ) == "https://svc.example/api/orders"
    # A path prefix on the deployment survives.
    assert proxy_logic.proxy_target(
        "https://x.example/hackproof/", "/api/healthz", ""
    ) == "https://x.example/hackproof/api/healthz"
    # Unconfigured: no target — the handler answers with the
    # designed not-connected body instead.
    assert proxy_logic.proxy_target("", "/api/orders") is None
    assert proxy_logic.proxy_target("  ", "/api/orders") is None


def test_cert_request_normalization_bridges_page_shape():
    """The page nests integrity inside payload and sends no
    license_key; the service requires both at top level. The proxy
    must produce the service's shape using the vault key, without
    disturbing the page's own fields."""
    out = proxy_logic.normalize_cert_request(PAGE_CERT_BODY, "VAULT-KEY")
    assert out == {
        "email": "student@example.com",
        "certificate_code": "CERT-1",
        "payload": {
            "integrity": {"version": 1, "verdict": "clean", "events": 0},
            "fullName": "A Student",
            "scorePct": 95,
        },
        "integrity": {"version": 1, "verdict": "clean", "events": 0},
        "license_key": "VAULT-KEY",
    }
    # The sender's dict is never mutated.
    assert "integrity" not in PAGE_CERT_BODY
    assert "license_key" not in PAGE_CERT_BODY


def test_cert_request_normalization_never_overrides():
    body = {
        "email": "a@b.co", "certificate_code": "C",
        "license_key": "PAGE-KEY", "integrity": {"verdict": "flagged"},
        "payload": {"integrity": {"verdict": "clean"}},
    }
    out = proxy_logic.normalize_cert_request(body, "VAULT")
    assert out["license_key"] == "PAGE-KEY"
    assert out["integrity"] == {"verdict": "flagged"}


def test_cert_request_passthrough_when_not_a_dict():
    blob = b"\x89not json"
    assert proxy_logic.normalize_cert_request(blob, "K") == blob
    plain = {"email": "a@b.co"}
    assert proxy_logic.normalize_cert_request(plain, "") == plain
    # No vault key: nothing invented (integrity still lifts).
    out = proxy_logic.normalize_cert_request(dict(PAGE_CERT_BODY), None)
    assert "license_key" not in out
    assert out["integrity"]["verdict"] == "clean"


def test_cert_response_normalization_held():
    out = proxy_logic.normalize_cert_response(
        {"status": "held_for_review", "cert_id": "c2"}
    )
    assert out["status"] == "held"
    # The raw service status stays available for richer consumers.
    assert out["service_status"] == "held_for_review"


def test_cert_response_issued_untouched():
    body = {"status": "issued", "cert_id": "c1"}
    out = proxy_logic.normalize_cert_response(body)
    assert out == {"status": "issued", "cert_id": "c1"}
    assert proxy_logic.normalize_cert_response("raw") == "raw"


def test_not_configured_body_is_designed():
    assert "error" in proxy_logic.NOT_CONFIGURED_BODY
