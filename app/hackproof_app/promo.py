"""Promo / test access codes: reconstructing the promo license.

The promo license is a REAL license (see ``tools/keygen.py``):
its per-license secret ``S`` is derived from the short code the
owner hands out — ``PBKDF2-HMAC-SHA256(code, salt, iterations)``
— instead of being random, and the pack build publishes
everything except ``S`` as ``promo-meta.json`` (KDF salt and
parameters, the signed license fields, and the Ed25519
signature over them). The metadata ships inside the app's
bundled webroot; the code itself is never in the app, the site,
or the repository in plaintext — it is built into the owner's
keygen tooling in concealed (sealed) form, and ``build-pack``
derives the promo license from it on the owner's machine. The
promo is an app-only feature: the website carries none of it.

Reconstruction is: derive ``S`` from the typed code, rebuild the
exact license object, and check the signature with the same
pure-Python verifier as any key (:mod:`hackproof_app.license_keys`).
A wrong code derives the wrong ``S`` and fails the signature —
the same refusal a forged key gets. The returned key string is
indistinguishable from a minted license downstream: it is stored
in the same vault slot, drives the same premium state, and is
what the proxy injects into certificate submissions, so a
certificate earned under promo countersigns through the standard
path (the service verifies the license's signature and the
payload's HMAC proof exactly as for a purchased key).

This module is pure logic (no Qt, no I/O beyond reading the
metadata file) so it is unit-tested directly. Attempt throttling
lives here as pure functions; the page persists the counters in
the settings store.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path

from . import license_keys
from .license_keys import LicenseError

#: The metadata file the pack build writes into the app's layer
#: of the tree (app/promo-meta.json); the bundler ships it at the
#: webroot root, beside the app's manifest.
META_NAME = "promo-meta.json"

KDF_NAME = "PBKDF2-HMAC-SHA256"

#: Sanity bound on the metadata's iteration count — the real
#: value is the keygen's 600k; a hand-edited or hostile metadata
#: file must not be able to stall the unlock for minutes.
MAX_ITERATIONS = 10_000_000

#: User-facing verdicts.
INACTIVE_MESSAGE = "Promo access isn't available in this edition."
WRONG_CODE_MESSAGE = "That code didn't work — check the digits and try again."


def load_meta(root: Path | None) -> dict | None:
    """The promo metadata from a webroot, or None.

    None covers every "no promo here" state: no webroot, no
    file, a ``null`` file (the state the repository ships until
    the owner's first pack build), unreadable JSON, or metadata
    that fails shape validation. The promo card renders its
    designed not-active state for all of them."""
    if root is None:
        return None
    try:
        raw = json.loads((Path(root) / META_NAME).read_text(
            encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    try:
        return validate_meta(raw)
    except LicenseError:
        return None


def validate_meta(meta) -> dict:
    """Shape-check promo metadata; returns it unchanged.

    Raises :class:`LicenseError` (edition wording — a malformed
    metadata file is an edition problem, never the user's fault)
    on anything unexpected."""
    if not isinstance(meta, dict):
        raise LicenseError(INACTIVE_MESSAGE)
    lic = meta.get("license")
    iterations = meta.get("iterations")
    if (
        meta.get("v") != 1
        or meta.get("kdf") != KDF_NAME
        or not isinstance(lic, dict)
        or not isinstance(lic.get("id"), str)
        or lic.get("tier") != "premium"
        or not isinstance(lic.get("expiry"), (int, float))
        or isinstance(lic.get("expiry"), bool)
        or not isinstance(lic.get("wrapped_Kc"), str)
        or not isinstance(meta.get("salt"), str)
        or not isinstance(meta.get("sig"), str)
        or not isinstance(iterations, int)
        or isinstance(iterations, bool)
        or not 1 <= iterations <= MAX_ITERATIONS
    ):
        raise LicenseError(INACTIVE_MESSAGE)
    try:
        salt = base64.b64decode(meta["salt"].encode("ascii"))
        sig = base64.b64decode(meta["sig"].encode("ascii"))
    except Exception:
        raise LicenseError(INACTIVE_MESSAGE) from None
    if len(salt) != 16 or len(sig) != 64:
        raise LicenseError(INACTIVE_MESSAGE)
    return meta


def derive_secret(code: str, salt: bytes, iterations: int) -> bytes:
    """S from a code: the one-way derivation every client pays
    identically (the keygen's parameters ship in the metadata)."""
    return hashlib.pbkdf2_hmac(
        "sha256", code.encode("utf-8"), salt, iterations, dklen=32
    )


def derive_promo_key(code: str, meta, public_key_hex: str) -> str:
    """Reconstruct the promo license key string from a typed code.

    Raises :class:`LicenseError` with user-facing wording on any
    refusal. On success the result is a standard license key —
    callers verify it with
    :func:`hackproof_app.license_keys.verify_license` like any
    other key (expiry and the clock guard apply identically)."""
    meta = validate_meta(meta)
    clean = (code or "").strip()
    if not clean:
        raise LicenseError("Enter your promo / test code first.")
    if not public_key_hex or public_key_hex.startswith("REPLACE_WITH"):
        raise LicenseError(
            "This build isn't linked to licensing yet — check back soon."
        )
    salt = base64.b64decode(meta["salt"].encode("ascii"))
    sig = base64.b64decode(meta["sig"].encode("ascii"))
    secret = derive_secret(clean, salt, int(meta["iterations"]))
    lm = meta["license"]
    lic = {
        "id": lm["id"],
        "tier": lm["tier"],
        "expiry": lm["expiry"],
        "S": base64.b64encode(secret).decode("ascii"),
        "wrapped_Kc": lm["wrapped_Kc"],
    }
    try:
        public_key = bytes.fromhex(public_key_hex)
    except Exception:
        raise LicenseError(
            "This build isn't linked to licensing yet — check back soon."
        ) from None
    if not license_keys.ed25519_verify(
        public_key, sig, license_keys.canonical_fields(lic)
    ):
        raise LicenseError(WRONG_CODE_MESSAGE)
    full = dict(lic)
    full["sig"] = meta["sig"]
    return base64.b64encode(
        json.dumps(full, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")


def is_promo_info(info: license_keys.LicenseInfo | None, meta) -> bool:
    """True when a verified license is the promo license (its id
    is the one the metadata names). Drives the honest
    "Premium — promo access" status label."""
    if info is None or not isinstance(meta, dict):
        return False
    lic = meta.get("license")
    return isinstance(lic, dict) and lic.get("id") == info.id


# ---------------------------------------------------------- throttling

def throttle_wait_seconds(fail_count: int) -> int:
    """The wait imposed after *fail_count* consecutive failures:
    5s, 10s, 20s, ... capped at 300s. Zero before any failure."""
    if not fail_count or fail_count < 1:
        return 0
    return min(5 * 2 ** (fail_count - 1), 300)


def throttle_remaining(fail_count: int, last_fail_ms: int,
                       now_ms: int) -> int:
    """Seconds left in the current throttle window (0 = an
    attempt is allowed now)."""
    wait = throttle_wait_seconds(fail_count)
    if not wait or not last_fail_ms:
        return 0
    left = wait - (now_ms - last_fail_ms) / 1000.0
    return math.ceil(left) if left > 0 else 0
