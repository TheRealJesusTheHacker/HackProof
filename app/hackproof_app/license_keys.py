"""Premium license keys: parsing and verification, natively.

This mirrors the website's verifier (``shared.js`` / the game's
``License``) byte-for-byte in behavior:

- a key is ``base64(JSON{id, tier, expiry, S, wrapped_Kc, sig})``;
- ``sig`` is an Ed25519 signature over the canonical JSON of the
  other five fields, checked against the product public key (read
  from the bundled ``shared.js`` — see
  :mod:`hackproof_app.site_bundle` — so the app can never drift
  from the website's key);
- the tier must be ``premium`` and the expiry (device clock) must
  be in the future;
- the clock-rollback guard from shared.js applies identically:
  a successful verification records the highest device clock ever
  seen, and a clock later found rewound past it by more than 24 h
  is refused.

The Ed25519 verifier below is pure Python (standard library only,
RFC 8032 verification equation) — the app needs verify-only, and
keeping it dependency-free keeps the frozen build to one vendor
stack (PySide6), the kit's convention. It is validated in the
test suite against the RFC 8032 vectors and against real keys
minted by ``tools/keygen.py``.

The page in the web view still performs its own verification with
the website's code before unlocking premium content — this native
verifier drives the app's own screens (premium status, the unlock
button's verdict) and must agree with it exactly. Error messages
intentionally reuse the website's wording.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import time
from dataclasses import dataclass

# ----------------------------------------------------------------------
# Ed25519 verification (RFC 8032), pure Python
# ----------------------------------------------------------------------

_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, _Q - 2, _Q)


_D = (-121665 * _inv(121666)) % _Q
_D2 = (2 * _D) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1) % _Q
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q != 0:
        x = (x * _I) % _Q
    if x % 2 != 0:
        x = _Q - x
    return x


_BY = (4 * _inv(5)) % _Q
_BX = _xrecover(_BY)
# Base point in extended coordinates (X, Y, Z, T).
_B = (_BX, _BY, 1, (_BX * _BY) % _Q)
_IDENTITY = (0, 1, 1, 0)


def _point_add(P, Q):
    X1, Y1, Z1, T1 = P
    X2, Y2, Z2, T2 = Q
    A = (Y1 - X1) * (Y2 - X2) % _Q
    B = (Y1 + X1) * (Y2 + X2) % _Q
    C = 2 * _D * T1 * T2 % _Q
    D = 2 * Z1 * Z2 % _Q
    E = (B - A) % _Q
    F = (D - C) % _Q
    G = (D + C) % _Q
    H = (B + A) % _Q
    return (E * F % _Q, G * H % _Q, F * G % _Q, E * H % _Q)


def _scalarmult(P, e: int):
    result = _IDENTITY
    addend = P
    while e > 0:
        if e & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        e >>= 1
    return result


def _decode_point(data: bytes):
    """Decode a 32-byte point; None when it is not a valid point."""
    if len(data) != 32:
        return None
    bits = int.from_bytes(data, "little")
    y = bits & ((1 << 255) - 1)
    sign = (bits >> 255) & 1
    if y >= _Q:
        return None
    try:
        x = _xrecover(y)
    except Exception:
        return None
    if (-x * x + y * y - 1 - _D * x * x * y * y) % _Q != 0:
        return None
    if x % 2 != sign:
        x = _Q - x
    return (x, y, 1, (x * y) % _Q)


def _encode_point(P) -> bytes:
    X, Y, Z, _T = P
    zi = _inv(Z)
    x = X * zi % _Q
    y = Y * zi % _Q
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def ed25519_verify(public_key: bytes, signature: bytes, message: bytes) -> bool:
    """RFC 8032 verification. False for anything malformed — this
    function never raises on attacker-controlled input."""
    try:
        if len(public_key) != 32 or len(signature) != 64:
            return False
        point_r = _decode_point(signature[:32])
        point_a = _decode_point(public_key)
        if point_r is None or point_a is None:
            return False
        s = int.from_bytes(signature[32:], "little")
        if s >= _L:
            return False
        digest = hashlib.sha512(signature[:32] + public_key + message).digest()
        h = int.from_bytes(digest, "little") % _L
        left = _scalarmult(_B, s)
        right = _point_add(point_r, _scalarmult(point_a, h))
        return _encode_point(left) == _encode_point(right)
    except Exception:
        return False


# ----------------------------------------------------------------------
# The license scheme (mirrors shared.js License)
# ----------------------------------------------------------------------


class LicenseError(Exception):
    """A license refusal, in the website's own plain wording —
    safe to show the customer as-is."""

    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


@dataclass
class LicenseInfo:
    id: str
    tier: str
    expiry: int  # unix seconds
    secret: bytes  # the per-license S (32 bytes)

    @property
    def is_premium(self) -> bool:
        return self.tier == "premium"


def parse_license(key_text: str) -> dict:
    """Parse a pasted key into its JSON object (no verification)."""
    clean = re.sub(r"\s+", "", key_text or "")
    if not clean:
        raise LicenseError("Paste your premium license key first.")
    try:
        obj = json.loads(base64.b64decode(clean).decode("utf-8"))
    except Exception:
        raise LicenseError(
            "That key is garbled — check for typos and try again."
        ) from None
    if not isinstance(obj, dict):
        raise LicenseError(
            "That key is garbled — check for typos and try again."
        )
    for field in ("id", "tier", "expiry", "S", "wrapped_Kc", "sig"):
        if field not in obj:
            raise LicenseError("That key is missing fields.")
    return obj


def canonical_fields(lic: dict) -> bytes:
    """The exact bytes the signature covers (keygen.py /
    shared.js agree: fixed field order, compact separators)."""
    return json.dumps(
        {
            "id": lic["id"],
            "tier": lic["tier"],
            "expiry": lic["expiry"],
            "S": lic["S"],
            "wrapped_Kc": lic["wrapped_Kc"],
        },
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


CLOCK_GUARD_TOLERANCE_MS = 24 * 60 * 60 * 1000


def verify_license(
    key_text: str,
    public_key_hex: str,
    *,
    now_ms: int | None = None,
    high_water_ms: int = 0,
) -> LicenseInfo:
    """Verify a key exactly the way the website does.

    Raises :class:`LicenseError` with the website's wording on any
    refusal. On success returns :class:`LicenseInfo`; the caller
    is responsible for persisting the clock high-water mark
    (``max(high_water_ms, now)``) as shared.js does.
    """
    if not public_key_hex or public_key_hex.startswith("REPLACE_WITH"):
        raise LicenseError(
            "This build isn't linked to licensing yet — check back soon."
        )
    lic = parse_license(key_text)
    if lic.get("tier") != "premium":
        raise LicenseError("That key isn't a premium license.")
    try:
        public_key = bytes.fromhex(public_key_hex)
        signature = base64.b64decode(str(lic["sig"]).encode("ascii"))
    except Exception:
        raise LicenseError(
            "Signature check failed — that key isn't genuine."
        ) from None
    if not ed25519_verify(public_key, signature, canonical_fields(lic)):
        raise LicenseError("Signature check failed — that key isn't genuine.")
    now = int(time.time() * 1000) if now_ms is None else int(now_ms)
    expiry = lic.get("expiry")
    if not isinstance(expiry, (int, float)) or isinstance(expiry, bool):
        raise LicenseError("This license has expired.")
    if expiry * 1000 <= now:
        raise LicenseError("This license has expired.")
    # Clock-rollback guard (shared.js clockGuard, same tolerance).
    if high_water_ms and now < high_water_ms - CLOCK_GUARD_TOLERANCE_MS:
        raise LicenseError(
            "Your device clock moved backward past the last verified "
            "time — restore the correct date and time to use your license."
        )
    try:
        secret = base64.b64decode(str(lic["S"]).encode("ascii"))
    except Exception:
        raise LicenseError(
            "That key is garbled — check for typos and try again."
        ) from None
    if len(secret) != 32:
        raise LicenseError(
            "That key is garbled — check for typos and try again."
        )
    return LicenseInfo(
        id=str(lic["id"]), tier=str(lic["tier"]),
        expiry=int(expiry), secret=secret,
    )


_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def public_key_hex_from_shared_js(text: str) -> str | None:
    """Extract ``LICENSE_PUBLIC_KEY_HEX`` from the bundled
    shared.js source. Returns None when absent or still the
    placeholder — verification then refuses with the designed
    "isn't linked to licensing yet" message, like the site."""
    match = re.search(
        r"LICENSE_PUBLIC_KEY_HEX\s*:\s*\"([0-9a-fA-F]{64})\"", text or ""
    )
    if not match:
        return None
    value = match.group(1)
    return value.lower() if _HEX64.match(value) else None
