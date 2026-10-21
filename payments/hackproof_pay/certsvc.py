"""Certificate auto-issuance.

POST /api/certificates lands here. The payload is validated with
EXACTLY the checks tools/keygen.py sign-cert enforces (see
crypto_core.validate_cert_payload) — forged or inconsistent payloads
are rejected no matter what the integrity block claims.

Then the integrity verdict decides:
  clean   -> countersign server-side, generate the finished
             certificate, email it. Idempotent: one certificate per
             (license, cert_id); resubmission returns the existing
             issuance, never a second one.
  flagged -> DO NOT auto-send. The validated payload is held in the
  (or missing/unreadable)   owner review queue; the owner countersigns
             manually with tools/keygen.py sign-cert. This hold is a
             deliberate design choice: automation must never rubber-
             stamp an exam the integrity layer questioned.
"""

from __future__ import annotations

import json
import logging

from . import crypto_core
from .certgen import certificate_filename, render_certificate_html
from .mailer import certificate_email_body
from .watcher import EMAIL_RE

log = logging.getLogger("hackproof_pay.certsvc")

# The exam builds its payload in this exact key order (proof last).
EXAM_KEY_ORDER = ["v", "cert_id", "name", "score", "pct", "date",
                  "lic_id", "proof"]

_CLEAN_WORDS = {"clean", "pass", "passed", "ok", "clear", "none"}


def integrity_verdict(block):
    """Reduce the site's integrity block to 'clean' or 'flagged'.

    Fail-closed: anything we cannot positively read as clean is
    flagged and held for the owner.
    """
    if not isinstance(block, dict):
        return "flagged"
    for key in ("verdict", "status", "result"):
        value = block.get(key)
        if isinstance(value, str) and value.strip():
            return ("clean" if value.strip().lower() in _CLEAN_WORDS
                    else "flagged")
    if block.get("clean") is True:
        return "clean"
    if block.get("flagged") is True:
        return "flagged"
    return "flagged"


def normalize_payload_object(payload):
    """Accept a payload submitted as a JSON object: apply the same
    unsigned-payload shape checks as a base64 code, and restore the
    exam's canonical key order when the field set matches."""
    if (not isinstance(payload, dict) or payload.get("v") != 1
            or "cert_id" not in payload or "name" not in payload
            or "sig" in payload):
        raise crypto_core.CertError(
            "not an unsigned HackProof certificate payload")
    if set(payload.keys()) == set(EXAM_KEY_ORDER):
        payload = {k: payload[k] for k in EXAM_KEY_ORDER}
    return payload


class CertificateError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class CertificateService:
    def __init__(self, cfg, store, keystore, mailer):
        self._cfg = cfg
        self._store = store
        self._keys = keystore
        self._mailer = mailer

    def submit(self, body):
        """Returns (http_status, response_dict)."""
        if not isinstance(body, dict):
            raise CertificateError("JSON object body required")
        # Same address rule as order creation (watcher.EMAIL_RE):
        # the address becomes an email header, so whitespace and
        # control characters — CRLF header injection above all —
        # must be refused here, not discovered inside the mailer
        # after the certificate has already been issued.
        email = body.get("email")
        if not isinstance(email, str):
            raise CertificateError(
                "a valid email is required — the certificate is "
                "delivered there")
        email = email.strip()
        if len(email) > 254 or not EMAIL_RE.match(email):
            raise CertificateError(
                "a valid email is required — the certificate is "
                "delivered there")
        license_key = body.get("license_key")
        if not isinstance(license_key, str):
            license_key = ""
        # ---- decode the payload (code form preferred: byte-exact) --
        code = body.get("certificate_code") or body.get("code")
        if not isinstance(code, str):
            code = None
        try:
            if code:
                payload = crypto_core.parse_cert_code(code)
            elif isinstance(body.get("payload"), dict):
                payload = normalize_payload_object(body["payload"])
            else:
                raise CertificateError(
                    "certificate_code (the code from the exam page) "
                    "is required")
            # ---- the full sign-cert validation, no shortcuts --------
            payload, lic_id = crypto_core.validate_cert_payload(
                self._keys, payload, license_key)
        except crypto_core.CertError as exc:
            raise CertificateError(str(exc))
        cert_id = payload["cert_id"]
        verdict = integrity_verdict(body.get("integrity"))
        if verdict != "clean":
            return self._hold(body, payload, email, license_key)
        return self._issue(payload, lic_id, email)

    # ------------------------------------------------------------- issue

    def _issue(self, payload, lic_id, email):
        store = self._store
        cert_id = payload["cert_id"]
        existing = store.get_certificate(lic_id, cert_id)
        if existing:
            if not existing["delivered"]:
                if self._send_cert_email(
                        existing, payload,
                        existing["countersigned_code"]):
                    store.set_certificate_delivered(lic_id, cert_id)
                    # Re-read: the response must report the delivery
                    # state as it now stands, not the stale row's.
                    existing = (store.get_certificate(lic_id, cert_id)
                                or existing)
            log.info("certificate resubmission — existing issuance "
                     "returned lic=%s cert=%s", lic_id, cert_id)
            return 200, self._issued_response(existing)
        countersigned = crypto_core.countersign(self._keys, payload)
        cert_html = render_certificate_html(payload,
                                            self._cfg["verify_url"])
        row = store.add_certificate({
            "lic_id": lic_id, "cert_id": cert_id, "email": email,
            "name": payload.get("name"), "score": payload.get("score"),
            "pct": payload.get("pct"), "cert_date": payload.get("date"),
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "countersigned_code": countersigned,
            "cert_html": cert_html, "delivered": False,
        })
        if row["countersigned_code"] != countersigned:
            # Lost a race with a duplicate submission — the stored
            # issuance is the only issuance.
            return 200, self._issued_response(row)
        sent = self._send_cert_email(row, payload, countersigned)
        if sent:
            store.set_certificate_delivered(lic_id, cert_id)
            # Re-read so the response's "delivered" flag is the
            # stored truth — the row above predates the send and
            # would report delivered=false for a certificate that
            # was in fact just emailed (sweep #3 finding).
            row = store.get_certificate(lic_id, cert_id) or row
        log.info("certificate ISSUED lic=%s cert=%s delivered=%s",
                 lic_id, cert_id, sent)
        return 201, self._issued_response(row)

    def _issued_response(self, row):
        return {
            "status": "issued",
            "cert_id": row["cert_id"],
            "countersigned_code": row["countersigned_code"],
            "verify_url": self._cfg["verify_url"],
            "delivered": bool(row.get("delivered")),
        }

    def _send_cert_email(self, row, payload, countersigned):
        body = certificate_email_body(self._cfg, payload, countersigned)
        return self._mailer.send(
            row["email"],
            "Your Sentinel Safeguard Certificate of Cyber Security "
            "Awareness Course Completion",
            body,
            attachments=[(certificate_filename(payload),
                          row["cert_html"].encode("utf-8"),
                          "text", "html")])

    # -------------------------------------------------------------- hold

    def _hold(self, body, payload, email, license_key):
        item = {
            "lic_id": payload.get("lic_id"),
            "cert_id": payload.get("cert_id"),
            "email": email,
            "name": payload.get("name"),
            "score": payload.get("score"),
            "pct": payload.get("pct"),
            "payload_json": json.dumps(payload, ensure_ascii=False),
            "license_key": license_key,
            "integrity_json": json.dumps(body.get("integrity"),
                                         ensure_ascii=False),
        }
        row = self._store.enqueue_review(item)
        log.warning(
            "certificate HELD FOR OWNER REVIEW cert=%s lic=%s "
            "integrity=%s — NOT auto-issued; owner countersigns "
            "manually with tools/keygen.py sign-cert",
            item["cert_id"], item["lic_id"], item["integrity_json"])
        return 202, {
            "status": "held_for_review",
            "cert_id": item["cert_id"],
            "detail": ("the exam's integrity check flagged this "
                       "attempt, so the certificate was not issued "
                       "automatically. It is queued for manual review "
                       "by Sentinel Safeguard."),
        }
