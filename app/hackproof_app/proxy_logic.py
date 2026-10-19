"""The app proxy: pure logic behind the web view's /api forwarding.

The bundled website pages are built to call a service base URL
(their ``CERT_SERVICE_BASE_URL`` constant). Inside the app that
constant is rewired at bundle time to the app origin —
``hackproof://app`` — so page requests for ``/api/...`` land in
the app's scheme handler, which forwards them to the real service
base URL from Settings (:mod:`hackproof_app.config`). This module
holds the forwarding decisions as pure functions so they are
unit-tested without Qt or a network; the Qt handler in
:mod:`hackproof_app.gui.webview` is a thin shell over them.

COMPATIBILITY SHIM (documented, deliberate): the exam page's
submission body and the certificate service's contract currently
differ in three ways, found while building this app —

1. the page sends the integrity block INSIDE its ``payload``; the
   service reads a TOP-LEVEL ``integrity`` field and fail-closes
   to a review hold without one;
2. the page does not send ``license_key``; the service requires it
   to verify the certificate's HMAC proof (the app holds the
   student's key in its vault, so the proxy can supply it);
3. an early page checked for ``"held"`` while the service answers
   ``{"status": "held_for_review"}``. RESOLVED on the page side:
   the current exam page checks the service's own value (and the
   202 status, which this transport cannot carry — scheme-job
   replies are always status 200, so the page's body-based
   checks are the ones that fire in-app). The response therefore
   passes through UNCHANGED; renaming it to ``"held"`` would
   break the held state the page now renders correctly.

The proxy still normalizes (1) and (2) on the way in — both are
written to NEVER override a field the sender already provided,
so they are no-ops on the current page's native shape and only
protect against older bundled pages.
"""

from __future__ import annotations

#: The origin the bundled pages are rewired to talk to.
APP_ORIGIN = "hackproof://app"
APP_HOST = "app"
APP_SCHEME = "hackproof"


def is_api_path(path: str) -> bool:
    """True for paths the proxy forwards to the service."""
    return path == "/api" or path.startswith("/api/")


def proxy_target(base_url: str, path: str, query: str = "") -> str | None:
    """The absolute service URL for an app-origin API path, or
    None when no service base is configured."""
    base = (base_url or "").strip().rstrip("/")
    if not base:
        return None
    url = base + path
    if query:
        url += "?" + query
    return url


def normalize_cert_request(body, license_key: str | None):
    """Prepare a page-originated POST /api/certificates body for
    the service (shim items 1 and 2 — see the module docstring).

    - lifts ``payload.integrity`` to a top-level ``integrity``
      when the top level is missing;
    - injects the vault's ``license_key`` when the body lacks one.
    A body that already carries either field is left untouched.
    Non-dict bodies pass through unchanged.
    """
    if not isinstance(body, dict):
        return body
    out = dict(body)
    if "integrity" not in out:
        payload = out.get("payload")
        if isinstance(payload, dict) and isinstance(
            payload.get("integrity"), dict
        ):
            out["integrity"] = payload["integrity"]
    if license_key and not out.get("license_key"):
        out["license_key"] = license_key
    return out


def normalize_cert_response(body):
    """Pass a service response through unchanged (shim item 3,
    resolved): the current page checks the service's own
    ``held_for_review`` value, and this transport always answers
    status 200, so the page's body-based branches — ``issued``
    and ``held_for_review`` — are the ones that fire in-app.
    Renaming anything here would break the held state."""
    return body


#: The body the proxy answers with when no service is configured:
#: the page renders its manual-route message from any non-issued,
#: non-held reply, which is the designed behavior.
NOT_CONFIGURED_BODY = {
    "error": "automatic delivery is not connected in this edition"
}
