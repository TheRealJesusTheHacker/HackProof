"""Cryptographic core — a faithful port of tools/keygen.py's schemes.

Everything license- or certificate-shaped in HackProof is defined by
tools/keygen.py. This module reproduces its formats byte-for-byte:

  License = base64( JSON {id, tier:"premium", expiry, S, wrapped_Kc, sig} )
    S          = fresh 256-bit random per license (base64)
    wrapped_Kc = base64( iv_w || AES-256-GCM(Kw, iv_w, Kc) )
    Kw         = HKDF-SHA256(S, salt="", info="hackproof-wrap", 32 bytes)
    sig        = Ed25519(priv, canonical JSON of {id,tier,expiry,S,wrapped_Kc})

  Certificate countersigning (keygen `sign-cert`):
    payload validation (score 72-90 of 90, pct exactly consistent,
    lic_id bound to the provided license, HMAC-SHA256 proof over the
    canonical payload-without-proof keyed by the license secret S),
    then sig = Ed25519(priv, canonical JSON of the full payload),
    output = base64( JSON {"payload": payload, "sig": sig} ).

The only deliberate difference from keygen.py: where keygen calls
sys.exit("REFUSING: ..."), this module raises typed errors so the HTTP
layer can answer cleanly. The checks, their order, and every byte that
gets signed are identical — tests prove it against keygen itself
(tests/test_payments.py imports the real tools/keygen.py and runs the
same accept/refuse matrix through both implementations).

Key custody: the private signing key and the master content key are
read from the host's existing key store (~/.hackproof, mode 600 files
written by `keygen.py setup`). They are never copied anywhere else,
never logged, and never leave this process except inside the license /
certificate artifacts they sign.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time

WRAP_INFO = b"hackproof-wrap"  # same HKDF info string as keygen.py


class CryptoError(Exception):
    """Base class for crypto-core failures."""


class KeyStoreError(CryptoError):
    """The host key store is missing or corrupt — refuse to start."""


class LicenseError(CryptoError):
    """A license key failed parsing or verification."""


class CertError(CryptoError):
    """A certificate payload failed sign-cert validation."""


def _need_crypto():
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except ImportError as exc:  # pragma: no cover - environment problem
        raise KeyStoreError(
            "The 'cryptography' package is required (same dependency as "
            "tools/keygen.py): pip install cryptography"
        ) from exc
    return Ed25519PrivateKey, AESGCM, HKDF, hashes, serialization


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


# ---------------------------------------------------------------- key store

def key_paths(keydir):
    """Same filenames keygen.py uses inside ~/.hackproof."""
    return {
        "priv": os.path.join(keydir, "ed25519-private.key"),
        "pub": os.path.join(keydir, "ed25519-public.key"),
        "kc": os.path.join(keydir, "content-master.key"),
    }


class KeyStore:
    """The seller's keys, loaded once from the host key store."""

    def __init__(self, keydir, priv, kc, pub_bytes):
        self.keydir = keydir
        self._priv = priv
        self._kc = kc
        self.pub_bytes = pub_bytes

    @property
    def public_key(self):
        return self._priv.public_key()

    @property
    def public_key_hex(self):
        return self.pub_bytes.hex()

    def sign(self, data: bytes) -> bytes:
        return self._priv.sign(data)

    @property
    def content_key(self) -> bytes:
        return self._kc


def load_keystore(keydir) -> KeyStore:
    """Load (and sanity-check) the host key store.

    Refuses — with a clear, actionable message — when the store is
    absent or corrupt. The service must never start keyless: a payment
    service that cannot mint is worse than one that is down.
    """
    Ed25519PrivateKey, _, _, _, serialization = _need_crypto()
    keydir = os.path.expanduser(keydir)
    paths = key_paths(keydir)
    missing = [p for name, p in paths.items()
               if name in ("priv", "kc") and not os.path.exists(p)]
    if missing:
        raise KeyStoreError(
            "HackProof key store incomplete: missing %s. Run "
            "`python3 tools/keygen.py setup` on this host first — the "
            "payment service reads the SAME ~/.hackproof store and "
            "never generates its own keys." % ", ".join(missing))
    with open(paths["priv"], "rb") as f:
        seed = f.read()
    with open(paths["kc"], "rb") as f:
        kc = f.read()
    if len(seed) != 32 or len(kc) != 32:
        raise KeyStoreError(
            "Key files in %s look corrupt (expected 32 bytes each)." % keydir)
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    derived_pub = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if os.path.exists(paths["pub"]):
        with open(paths["pub"], "rb") as f:
            stored_pub = f.read()
        if stored_pub != derived_pub:
            raise KeyStoreError(
                "ed25519-public.key in %s does not match the private "
                "key — the store is inconsistent; refusing to start."
                % keydir)
    return KeyStore(keydir, priv, kc, derived_pub)


# ---------------------------------------------------------------- licenses

def canonical_fields(lic) -> str:
    """Byte-identical to keygen.canonical_fields (fixed key order)."""
    return json.dumps(
        {"id": lic["id"], "tier": lic["tier"], "expiry": lic["expiry"],
         "S": lic["S"], "wrapped_Kc": lic["wrapped_Kc"]},
        separators=(",", ":"))


def mint_license(store: KeyStore, days: int = 365, tier: str = "premium"):
    """Mint one license — byte-compatible with `keygen.py mint`.

    Returns (license_key_string, license_dict). Raises CryptoError for
    the same inputs keygen refuses (non-premium tier, days outside
    1..3650).
    """
    _, AESGCM, HKDF, hashes, _ = _need_crypto()
    if tier not in ("premium",):
        raise CryptoError("tier must be 'premium' (free needs no license)")
    if not 1 <= int(days) <= 3650:
        raise CryptoError(
            "--days must be between 1 and 3650 (got %r)" % (days,))
    S = os.urandom(32)
    kw = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"",
              info=WRAP_INFO).derive(S)
    iv_w = os.urandom(12)
    wrapped = iv_w + AESGCM(kw).encrypt(iv_w, store.content_key, None)
    lic = {
        "id": b64e(os.urandom(6)),
        "tier": tier,
        "expiry": int(time.time()) + int(days) * 86400,
        "S": b64e(S),
        "wrapped_Kc": b64e(wrapped),
    }
    sig = store.sign(canonical_fields(lic).encode("utf-8"))
    lic["sig"] = b64e(sig)
    license_key = b64e(
        json.dumps(lic, separators=(",", ":")).encode("utf-8"))
    return license_key, lic


def parse_and_verify_license(store: KeyStore, license_key: str):
    """Verify a license key the way the site (and keygen) does.

    Returns (license_dict, S_bytes). Raises LicenseError otherwise.
    Mirrors keygen.license_secret_from_key: structure, tier, Ed25519
    signature over the canonical fields, S must decode to 32 bytes.
    """
    clean = re.sub(r"\s+", "", license_key or "")
    try:
        lic = json.loads(base64.b64decode(clean).decode("utf-8"))
    except Exception:
        raise LicenseError("the license key is not valid base64/JSON")
    if not isinstance(lic, dict):
        raise LicenseError("the license key is not a license object")
    for k in ("id", "tier", "expiry", "S", "wrapped_Kc", "sig"):
        if k not in lic:
            raise LicenseError("the license key is missing fields")
    if lic.get("tier") != "premium":
        raise LicenseError("the license key is not a premium license")
    canonical = canonical_fields(lic)
    try:
        sig = base64.b64decode(lic["sig"].encode("ascii"))
        store.public_key.verify(sig, canonical.encode("utf-8"))
    except Exception:
        raise LicenseError(
            "the license key's signature does not verify — "
            "not a genuine HackProof license")
    try:
        S = base64.b64decode(lic["S"].encode("ascii"))
    except Exception:
        raise LicenseError("the license key has a garbled S field")
    if len(S) != 32:
        raise LicenseError("the license key's S field is not 32 bytes")
    return lic, S


def unwrap_content_key(store_pub_verify_only, lic) -> bytes:
    """Recover Kc from a license — what the game does after verifying.

    Used by tests to prove a service-minted key actually unlocks the
    pack scheme: HKDF(S) -> AES-256-GCM decrypt of wrapped_Kc.
    (store_pub_verify_only is unused; kept for a symmetric signature
    with parse_and_verify_license call sites in tests.)
    """
    _, AESGCM, HKDF, hashes, _ = _need_crypto()
    S = base64.b64decode(lic["S"].encode("ascii"))
    kw = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"",
              info=WRAP_INFO).derive(S)
    wrapped = base64.b64decode(lic["wrapped_Kc"].encode("ascii"))
    iv_w, ct = wrapped[:12], wrapped[12:]
    return AESGCM(kw).decrypt(iv_w, ct, None)


# ------------------------------------------------------------- certificates

def parse_cert_code(code: str) -> dict:
    """Decode an unsigned certificate code — keygen's first checks."""
    clean = re.sub(r"\s+", "", code or "")
    try:
        payload = json.loads(base64.b64decode(clean).decode("utf-8"))
    except Exception:
        raise CertError("not a valid certificate code (bad base64/JSON)")
    if (not isinstance(payload, dict) or payload.get("v") != 1
            or "cert_id" not in payload or "name" not in payload
            or "sig" in payload):
        raise CertError("not an unsigned HackProof certificate payload")
    return payload


def validate_cert_payload(store: KeyStore, payload: dict, license_key: str):
    """The full sign-cert validation, in keygen's exact order.

    Raises CertError with keygen's refusal reasons. On success returns
    (payload, lic_id) — the payload is then safe to countersign.
    """
    # 1) score fields: integers (bool is not an int), a passing score
    #    the exam could have issued, pct exactly consistent.
    for field in ("score", "pct"):
        val = payload.get(field)
        if isinstance(val, bool) or not isinstance(val, int):
            raise CertError(
                "score field %r must be an integer (got %r)" % (field, val))
    score, pct = payload["score"], payload["pct"]
    if not 72 <= score <= 90:
        raise CertError(
            "score %r is not a passing exam score (72-90 of 90)" % (score,))
    # Math.round(score / 90 * 100) with JS half-up rounding, in integers.
    expected_pct = (score * 200 + 90) // 180
    if pct != expected_pct:
        raise CertError(
            "pct %r does not match score %r (the exam would have "
            "issued %d)" % (pct, score, expected_pct))
    # 2) HMAC proof must be present and well-formed (verified below).
    proof_b64 = payload.get("proof")
    if not isinstance(proof_b64, str) or not proof_b64:
        raise CertError(
            "certificate code has no HMAC proof — it was not generated "
            "by the current exam page")
    if not license_key:
        raise CertError(
            "the student's license key is required to verify the "
            "certificate's HMAC proof")
    try:
        lic, S = parse_and_verify_license(store, license_key)
    except LicenseError as exc:
        raise CertError(str(exc))
    lic_id = lic["id"]
    # 3) the payload must name the very license that earned it
    if payload.get("lic_id") != lic_id:
        raise CertError(
            "the certificate's lic_id %r does not match the license "
            "key provided (%r) — code and key must come from the same "
            "student" % (payload.get("lic_id"), lic_id))
    # 4) HMAC-SHA256 proof over the canonical payload WITHOUT proof
    #    (proof was appended last by the exam, so dropping it restores
    #    the original key order — identical to keygen).
    body = {k: v for k, v in payload.items() if k != "proof"}
    canonical = json.dumps(body, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    try:
        proof = base64.b64decode(proof_b64.encode("ascii"))
    except Exception:
        raise CertError("proof is not valid base64")
    expected = hmac.new(S, canonical, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, proof):
        raise CertError(
            "HMAC proof does not verify — this payload was "
            "hand-crafted, not produced by the exam with a genuine "
            "license. No signature issued")
    return payload, lic_id


def countersign(store: KeyStore, payload: dict) -> str:
    """Countersign a validated payload — byte-identical to keygen."""
    canonical_full = json.dumps(payload, separators=(",", ":"),
                                ensure_ascii=False).encode("utf-8")
    sig = store.sign(canonical_full)
    signed = {"payload": payload, "sig": b64e(sig)}
    return b64e(json.dumps(signed, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8"))


def verify_countersigned(pubkey_bytes: bytes, countersigned_code: str):
    """Verify a countersigned code the way exam.html/verify.html do.

    Returns the payload dict on success, raises CertError otherwise.
    (Browser semantics: Ed25519 over JSON.stringify(payload) — i.e.
    json.dumps with separators (",", ":") and raw UTF-8.)
    """
    Ed25519PrivateKey, _, _, _, _ = _need_crypto()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey,
    )
    clean = re.sub(r"\s+", "", countersigned_code or "")
    try:
        raw = json.loads(base64.b64decode(clean).decode("utf-8"))
        payload = raw["payload"]
        sig = base64.b64decode(raw["sig"].encode("ascii"))
    except Exception:
        raise CertError("not a countersigned certificate code")
    canonical = json.dumps(payload, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    try:
        Ed25519PublicKey.from_public_bytes(pubkey_bytes).verify(
            sig, canonical)
    except Exception:
        raise CertError("countersignature does not verify")
    return payload
