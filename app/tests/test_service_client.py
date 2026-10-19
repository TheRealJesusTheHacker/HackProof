"""ServiceClient against a stub transport: the exact contract
shapes from payments/ (routes, fields, statuses, the top-level
integrity rule) and the two-voice error mapping."""

from __future__ import annotations

import pytest

from hackproof_app.service_client import (
    CertificateResult,
    ServiceClient,
    ServiceError,
    ServiceNotConfigured,
    ServiceRejected,
    ServiceUnreachable,
)

ORDER_BODY = {
    "order_id": "hp_0123456789abcdef01234567",
    "status": "awaiting_payment",
    "btc_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "btc_amount_sats": 6123,
    "btc_amount_btc": "0.00006123",
    "price_usd": 5.0,
    "confirmations": 0,
    "expires_at": "2030-01-01T00:00:00Z",
}


class StubTransport:
    """The transport contract: (method, url, body, timeout) ->
    (status, parsed_json|None); network failure is raised as
    ServiceUnreachable, exactly like the real urllib transport."""

    def __init__(self, routes):
        self.routes = routes  # (method, suffix) -> (status, body) or exc
        self.calls = []

    def __call__(self, method, url, body, timeout):
        self.calls.append((method, url, body))
        for (m, suffix), outcome in self.routes.items():
            if m == method and url.endswith(suffix):
                if isinstance(outcome, BaseException):
                    raise outcome
                return outcome
        raise AssertionError(f"no stub route for {method} {url}")


def client(routes, base="https://svc.example"):
    return ServiceClient(base, transport=StubTransport(routes))


def test_create_order_parses_contract():
    c = client({("POST", "/api/orders"): (201, ORDER_BODY)})
    order = c.create_order("buyer@example.com")
    assert order.order_id == ORDER_BODY["order_id"]
    assert order.btc_amount_sats == 6123
    assert order.status == "awaiting_payment"
    assert not order.is_paid
    method, url, body = c._transport.calls[0]
    assert body == {"email": "buyer@example.com"}


def test_get_order_paid_surfaces_key_and_delivery():
    paid = dict(ORDER_BODY, status="paid", confirmations=1,
                license_key="THEKEY", delivery="emailed")
    c = client({("GET", "/api/orders/" + ORDER_BODY["order_id"]): (200, paid)})
    order = c.get_order(ORDER_BODY["order_id"])
    assert order.is_paid and order.license_key == "THEKEY"
    assert order.delivery == "emailed"


def test_expired_order_status():
    c = client({("GET", "/x"): (200, dict(ORDER_BODY, status="expired"))})
    assert c.get_order("x").status == "expired"


def test_unconfigured_client_plain_refusal():
    c = ServiceClient("")
    assert not c.configured
    assert c.health() is False
    with pytest.raises(ServiceNotConfigured) as exc:
        c.create_order("a@b.co")
    assert "aren't connected in this copy" in exc.value.user_message


def test_unreachable_and_bad_responses_are_two_voice():
    c = client({("POST", "/api/orders"): ServiceUnreachable(detail="boom")})
    with pytest.raises(ServiceUnreachable) as exc:
        c.create_order("a@b.co")
    assert "couldn't reach the service" in exc.value.user_message
    assert exc.value.detail == "boom"

    c = client({("POST", "/api/orders"): (502, None)})
    with pytest.raises(ServiceRejected) as exc:
        c.create_order("a@b.co")
    assert exc.value.status == 502
    assert "couldn't complete that" in exc.value.user_message

    c = client({("POST", "/api/orders"): (201, {"unexpected": True})})
    with pytest.raises(ServiceError) as exc:
        c.create_order("a@b.co")
    assert "couldn't read" in exc.value.user_message


def test_server_rejection_passes_through_its_message():
    c = client({("POST", "/api/orders"): (400, {"error": "bad email"})})
    with pytest.raises(ServiceRejected) as exc:
        c.create_order("a@b.co")
    assert exc.value.user_message == "bad email"
    assert exc.value.status == 400


def test_health_contract():
    c = client({("GET", "/healthz"): (200, {"ok": True})})
    assert c.health() is True
    c = client({("GET", "/healthz"): (503, None)})
    assert c.health() is False
    c = client({("GET", "/healthz"): ServiceUnreachable()})
    assert c.health() is False


ISSUED = {
    "status": "issued",
    "cert_id": "cert-1",
    "countersigned_code": "SS-HP-AAAA-BBBB",
    "verify_url": "https://hackproof.example/verify.html?c=SS-HP",
    "delivered": "emailed",
}
HELD = {
    "status": "held_for_review",
    "cert_id": "cert-2",
    "detail": "This certificate is with a person for review.",
}
INTEGRITY = {"version": 1, "verdict": "clean", "events": 0}


def test_certificate_issued_and_held():
    c = client({("POST", "/api/certificates"): (201, ISSUED)})
    result = c.submit_certificate(
        email="a@b.co", license_key="KEY", certificate_code="CODE",
        integrity=INTEGRITY,
    )
    assert isinstance(result, CertificateResult)
    assert result.is_issued and not result.is_held
    assert result.countersigned_code.startswith("SS-HP-")
    assert result.delivered  # "emailed" is truthy
    # The outgoing body must carry the documented raw shape:
    # integrity TOP-LEVEL (the service fail-closes without it).
    method, url, body = c._transport.calls[0]
    assert body == {
        "email": "a@b.co",
        "license_key": "KEY",
        "certificate_code": "CODE",
        "integrity": INTEGRITY,
    }

    c = client({("POST", "/api/certificates"): (202, HELD)})
    result = c.submit_certificate(
        email="a@b.co", license_key="KEY", certificate_code="CODE",
        integrity=INTEGRITY,
    )
    assert result.is_held and not result.is_issued
    assert "person for review" in result.detail
