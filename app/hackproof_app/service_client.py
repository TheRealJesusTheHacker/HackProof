"""Client for the HackProof payments/certificate service.

The contract (owned by the payments crew, ``payments/`` in this
repository — implemented in ``payments/hackproof_pay/httpd.py``):

- ``POST /api/orders`` ``{"email"}`` → ``201`` with the public
  order: ``{order_id, status, btc_address, btc_amount_sats,
  btc_amount_btc, price_usd, confirmations, expires_at}``.
  Statuses: ``awaiting_payment`` → ``confirming`` → ``paid`` /
  ``expired``. Once ``paid``, the same object also carries
  ``license_key`` and ``delivery`` (the order id is the claim
  credential — whoever holds it may retrieve the key).
- ``GET /api/orders/<order_id>`` → the same public order.
- ``POST /api/certificates`` ``{email, license_key,
  certificate_code, integrity}`` → ``201``/``200``
  ``{"status": "issued", cert_id, countersigned_code, verify_url,
  delivered}``, or ``202`` ``{"status": "held_for_review", cert_id,
  detail}`` when the integrity verdict is not clean, or a 4xx
  ``{"error": ...}`` refusal with the service's plain-language
  reason.
- ``GET /healthz`` → ``{"ok": true}``.

The transport is an injectable seam (``transport(method, url,
json_body) -> (status, parsed_json)``) so every behavior above is
unit-tested without a network. The default transport is urllib
from the standard library — no dependency joins the build for
this.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_TIMEOUT_SECONDS = 15.0


class ServiceError(Exception):
    """A service failure in two voices, like the setup engine's:
    ``user_message`` is plain language for the screen; ``detail``
    is the technical record for logs/support."""

    def __init__(self, user_message: str, detail: str = ""):
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


class ServiceNotConfigured(ServiceError):
    def __init__(self):
        super().__init__(
            "Online services aren't connected in this copy of "
            "HackProof yet. The course and exam work fully — buying "
            "and automatic certificate delivery will light up when "
            "Sentinel Safeguard connects this edition.",
            detail="service base URL is empty",
        )


class ServiceUnreachable(ServiceError):
    def __init__(self, detail: str = ""):
        super().__init__(
            "HackProof couldn't reach the service just now. Check "
            "your internet connection and try again — nothing was "
            "charged or lost.",
            detail=detail,
        )


class ServiceRejected(ServiceError):
    """The service answered with an error of its own; its message
    is already plain language written for the customer."""

    def __init__(self, status: int, message: str):
        super().__init__(message, detail=f"HTTP {status}: {message}")
        self.status = status


@dataclass
class Order:
    order_id: str
    status: str
    btc_address: str
    btc_amount_sats: int
    btc_amount_btc: str
    price_usd: float
    confirmations: int
    expires_at: str
    license_key: str | None = None
    delivery: str | None = None

    @classmethod
    def from_json(cls, raw) -> "Order":
        if not isinstance(raw, dict) or "order_id" not in raw:
            raise ServiceError(
                "The service sent back an answer HackProof couldn't "
                "read. Try again in a moment.",
                detail=f"unexpected order payload: {raw!r}",
            )
        return cls(
            order_id=str(raw.get("order_id") or ""),
            status=str(raw.get("status") or ""),
            btc_address=str(raw.get("btc_address") or ""),
            btc_amount_sats=int(raw.get("btc_amount_sats") or 0),
            btc_amount_btc=str(raw.get("btc_amount_btc") or ""),
            price_usd=float(raw.get("price_usd") or 0),
            confirmations=int(raw.get("confirmations") or 0),
            expires_at=str(raw.get("expires_at") or ""),
            license_key=(str(raw["license_key"])
                         if raw.get("license_key") else None),
            delivery=(str(raw["delivery"])
                      if raw.get("delivery") else None),
        )

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"


@dataclass
class CertificateResult:
    status: str  # "issued" | "held_for_review" (service vocabulary)
    cert_id: str
    countersigned_code: str | None = None
    verify_url: str | None = None
    delivered: bool = False
    detail: str = ""

    @property
    def is_issued(self) -> bool:
        return self.status == "issued"

    @property
    def is_held(self) -> bool:
        return self.status == "held_for_review"


def _urllib_transport(method, url, body, timeout):
    """Default transport: (status, parsed_json_or_None).

    Network-level failures raise ServiceUnreachable; an HTTP error
    status is RETURNED (with its parsed body) so the caller can
    surface the service's own message.
    """
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, _parse_json(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, _parse_json(raw)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise ServiceUnreachable(detail=repr(exc)) from exc


def _parse_json(raw):
    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


class ServiceClient:
    """One configured connection to the payments service."""

    def __init__(self, base_url: str, *, transport=None,
                 timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.base_url = (base_url or "").strip().rstrip("/")
        self._transport = transport or _urllib_transport
        self._timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _call(self, method, path, body=None):
        if not self.configured:
            raise ServiceNotConfigured()
        status, payload = self._transport(
            method, self.base_url + path, body, self._timeout
        )
        if status >= 400:
            message = (payload or {}).get("error") or (
                "The service couldn't complete that just now. "
                "Try again in a moment."
            )
            raise ServiceRejected(status, str(message))
        if payload is None:
            raise ServiceError(
                "The service sent back an answer HackProof couldn't "
                "read. Try again in a moment.",
                detail=f"{method} {path} -> HTTP {status}, non-JSON body",
            )
        return payload

    # ---------------------------------------------------------- orders

    def create_order(self, email: str) -> Order:
        payload = self._call("POST", "/api/orders", {"email": email})
        return Order.from_json(payload)

    def get_order(self, order_id: str) -> Order:
        payload = self._call("GET", f"/api/orders/{order_id}")
        return Order.from_json(payload)

    # ---------------------------------------------------- certificates

    def submit_certificate(self, *, email: str, license_key: str,
                           certificate_code: str | None = None,
                           payload: dict | None = None,
                           integrity: dict | None = None
                           ) -> CertificateResult:
        """Submit an exam completion for automatic issuance.

        Sends the service's raw contract: the integrity verdict is
        a TOP-LEVEL field (the service reads ``body["integrity"]``
        and fail-closes to a hold when it cannot read a clean
        verdict), and the student's license key travels with it
        (the service needs it to verify the certificate's HMAC
        proof — the same binding ``tools/keygen.py sign-cert``
        enforces).
        """
        body: dict = {"email": email, "license_key": license_key}
        if certificate_code:
            body["certificate_code"] = certificate_code
        if payload is not None:
            body["payload"] = payload
        if integrity is not None:
            body["integrity"] = integrity
        raw = self._call("POST", "/api/certificates", body)
        return CertificateResult(
            status=str(raw.get("status") or ""),
            cert_id=str(raw.get("cert_id") or ""),
            countersigned_code=(str(raw["countersigned_code"])
                                if raw.get("countersigned_code") else None),
            verify_url=(str(raw["verify_url"])
                        if raw.get("verify_url") else None),
            delivered=bool(raw.get("delivered")),
            detail=str(raw.get("detail") or ""),
        )

    # ---------------------------------------------------------- health

    def health(self) -> bool:
        """True when the service answers /healthz. Never raises —
        this backs the Settings "test connection" line."""
        if not self.configured:
            return False
        try:
            status, payload = self._transport(
                "GET", self.base_url + "/healthz", None, self._timeout
            )
        except ServiceError:
            return False
        return status == 200 and bool(payload and payload.get("ok"))
