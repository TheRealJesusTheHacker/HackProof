"""License verification: the app's pure-Python verifier must agree
with the production tooling (tools/keygen.py + the cryptography
library it uses) on genuine keys and on every refusal."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hackproof_app import license_keys
from hackproof_app.license_keys import LicenseError

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYGEN = REPO_ROOT / "tools" / "keygen.py"

# RFC 8032 TEST 1 (empty message) — the canonical published vector.
RFC_PK = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
)
RFC_SIG = bytes.fromhex(
    "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
    "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
)


def test_rfc8032_test_vector_1():
    assert license_keys.ed25519_verify(RFC_PK, RFC_SIG, b"") is True


def test_ed25519_rejects_tampering():
    forged = bytearray(RFC_SIG)
    forged[10] ^= 1
    assert license_keys.ed25519_verify(RFC_PK, bytes(forged), b"") is False
    assert license_keys.ed25519_verify(RFC_PK, RFC_SIG, b"x") is False
    assert license_keys.ed25519_verify(RFC_PK, RFC_SIG[:63], b"") is False
    assert license_keys.ed25519_verify(b"", RFC_SIG, b"") is False
    assert license_keys.ed25519_verify(RFC_PK, bytes(64), b"") is False
    assert license_keys.ed25519_verify(RFC_PK, b"garbage", b"") is False


def test_ed25519_cross_implementation():
    """Random keys/messages: our verifier must agree with the
    cryptography library (the one keygen.py signs with)."""
    cryptography = pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    _ = cryptography
    for i in range(12):
        priv = Ed25519PrivateKey.generate()
        pub = priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        message = os.urandom(i * 13)
        sig = priv.sign(message)
        assert license_keys.ed25519_verify(pub, sig, message) is True
        forged = bytearray(sig)
        forged[40] ^= 0x40
        assert license_keys.ed25519_verify(pub, bytes(forged), message) is False


def _load_keygen():
    spec = importlib.util.spec_from_file_location("hp_keygen", KEYGEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_fields_match_keygen():
    keygen = _load_keygen()
    lic = {
        "id": "abc123", "tier": "premium", "expiry": 1893456000,
        "S": "AAAA", "wrapped_Kc": "BBBB", "sig": "CCCC",
    }
    assert (
        license_keys.canonical_fields(lic).decode("utf-8")
        == keygen.canonical_fields(lic)
    )


@pytest.fixture(scope="module")
def minted(tmp_path_factory):
    """A REAL keypair + license from the repo's own keygen.py.

    Skips when the cryptography package isn't importable (it is
    keygen's only dependency, and a test-only one for the app)."""
    keydir = tmp_path_factory.mktemp("keydir")
    env = dict(os.environ)
    setup = subprocess.run(
        [sys.executable, str(KEYGEN), "setup", "--keydir", str(keydir)],
        capture_output=True, text=True, env=env,
    )
    if setup.returncode != 0:
        pytest.skip(f"keygen setup unavailable: {setup.stdout} {setup.stderr}")
    pub_hex = None
    for line in setup.stdout.splitlines():
        if "LICENSE_PUBLIC_KEY_HEX" in line:
            pub_hex = line.split('"')[1]
    assert pub_hex
    mint = subprocess.run(
        [sys.executable, str(KEYGEN), "mint", "--keydir", str(keydir),
         "--days", "365"],
        capture_output=True, text=True, env=env,
    )
    assert mint.returncode == 0, mint.stderr
    key = mint.stdout.splitlines()[1].strip()
    return {"pub_hex": pub_hex, "key": key}


def test_real_keygen_license_verifies(minted):
    info = license_keys.verify_license(minted["key"], minted["pub_hex"])
    assert info.is_premium
    assert len(info.secret) == 32
    assert info.expiry > 0


def test_real_license_tamper_refused(minted):
    raw = json.loads(base64.b64decode(minted["key"]).decode("utf-8"))
    raw["expiry"] += 10 * 365 * 86400  # extend without re-signing
    forged = base64.b64encode(json.dumps(raw).encode("utf-8")).decode()
    with pytest.raises(LicenseError) as exc:
        license_keys.verify_license(forged, minted["pub_hex"])
    assert "isn't genuine" in exc.value.user_message


def test_real_license_expiry_refused(minted):
    far_future_ms = (9999999999) * 1000
    with pytest.raises(LicenseError) as exc:
        license_keys.verify_license(
            minted["key"], minted["pub_hex"], now_ms=far_future_ms
        )
    assert "expired" in exc.value.user_message


def test_wrong_public_key_refused(minted):
    other = "00" * 32
    with pytest.raises(LicenseError):
        license_keys.verify_license(minted["key"], other)


def test_parse_errors_use_product_wording():
    with pytest.raises(LicenseError) as exc:
        license_keys.parse_license("")
    assert "Paste your premium license key" in exc.value.user_message
    with pytest.raises(LicenseError) as exc:
        license_keys.parse_license("not-a-key!!!")
    assert "garbled" in exc.value.user_message
    partial = base64.b64encode(json.dumps({"id": "x"}).encode()).decode()
    with pytest.raises(LicenseError) as exc:
        license_keys.parse_license(partial)
    assert "missing fields" in exc.value.user_message


def test_placeholder_public_key_refuses():
    with pytest.raises(LicenseError) as exc:
        license_keys.verify_license("AAAA", "")
    assert "isn't linked to licensing" in exc.value.user_message


def test_clock_guard(minted):
    import time

    now = int(time.time() * 1000)  # inside the minted key's validity
    info = license_keys.verify_license(
        minted["key"], minted["pub_hex"], now_ms=now, high_water_ms=now
    )
    assert info is not None
    rewound = now - 48 * 3600 * 1000  # 2 days back, past the 24h slack
    with pytest.raises(LicenseError) as exc:
        license_keys.verify_license(
            minted["key"], minted["pub_hex"],
            now_ms=rewound, high_water_ms=now,
        )
    assert "clock moved backward" in exc.value.user_message


def test_public_key_extraction_from_shared_js():
    text = 'LICENSE_PUBLIC_KEY_HEX: "' + "ab" * 32 + '"'
    assert license_keys.public_key_hex_from_shared_js(text) == "ab" * 32
    assert license_keys.public_key_hex_from_shared_js(
        'LICENSE_PUBLIC_KEY_HEX: "REPLACE_WITH_YOUR_PUBLIC_KEY_HEX"'
    ) is None
    assert license_keys.public_key_hex_from_shared_js("") is None
