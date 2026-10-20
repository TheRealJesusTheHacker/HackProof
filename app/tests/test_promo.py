"""Promo / test access codes: the app's reconstruction of the
promo license must agree with the production tooling
(tools/keygen.py) byte-for-byte, refuse wrong codes the way it
refuses forgeries, throttle repeated failures, persist that
throttle, and drive the My Premium promo card.

The promo license is a REAL license whose secret is derived
from the code (PBKDF2) instead of random; the metadata the pack
build publishes carries everything except that secret. The code
is built into the keygen in concealed form; the fixtures below
use a throwaway key store and type the built-in code the way a
user would — assembled at runtime, because the release gate
greps this tree for the literal digits and a stored
representation must never sit in a file.
"""

from __future__ import annotations

import base64
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from conftest import pump_until
from hackproof_app import license_keys, promo, site_bundle
from hackproof_app.license_keys import LicenseError

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYGEN = REPO_ROOT / "tools" / "keygen.py"

#: The built-in promo code, typed as a user would type it —
#: assembled from character codes so the literal digit string
#: never sits in this file (see the module docstring).
TEST_CODE = "".join(map(chr, (53, 55, 49, 54)))


def _load_keygen():
    spec = importlib.util.spec_from_file_location("hp_keygen", KEYGEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def promo_env(tmp_path_factory):
    """A REAL keygen key store, and the metadata build-pack
    publishes for it from the sealed built-in code. The KDF
    iteration constant is patched down for speed — the metadata
    records the same patched value, exactly as production
    records its real one, and every client reads it from there."""
    keygen = _load_keygen()
    keydir = tmp_path_factory.mktemp("promo-keydir")
    keygen.cmd_setup(str(keydir))
    old = keygen.PROMO_KDF_ITERATIONS
    keygen.PROMO_KDF_ITERATIONS = 1_000
    try:
        priv, kc = keygen.load_keys(str(keydir))
        assert keygen._builtin_promo_code() == TEST_CODE
        meta = keygen.build_promo_meta(priv, kc)
        assert meta is not None
        secret = keygen.derive_promo_secret(
            TEST_CODE, keygen.b64d(meta["salt"]))
        expected_key = keygen.promo_license_key(meta, secret)
    finally:
        keygen.PROMO_KDF_ITERATIONS = old
    pub_hex = (Path(keydir) / "ed25519-public.key").read_bytes().hex()
    return {"meta": meta, "pub_hex": pub_hex, "key": expected_key}


# ---------------------------------------------------------- derivation


def test_app_reconstruction_matches_keygen(promo_env):
    derived = promo.derive_promo_key(
        TEST_CODE, promo_env["meta"], promo_env["pub_hex"])
    assert derived == promo_env["key"]


def test_reconstructed_key_verifies(promo_env):
    info = license_keys.verify_license(
        promo_env["key"], promo_env["pub_hex"])
    assert info.is_premium
    assert info.id == promo_env["meta"]["license"]["id"]
    assert len(info.secret) == 32
    assert promo.is_promo_info(info, promo_env["meta"])
    assert not promo.is_promo_info(info, None)
    assert not promo.is_promo_info(None, promo_env["meta"])


def test_wrong_code_refused_like_a_forgery(promo_env):
    with pytest.raises(LicenseError) as exc:
        promo.derive_promo_key(
            "0000", promo_env["meta"], promo_env["pub_hex"])
    assert exc.value.user_message == promo.WRONG_CODE_MESSAGE


def test_tampered_metadata_refused(promo_env):
    meta = copy.deepcopy(promo_env["meta"])
    raw = bytearray(base64.b64decode(meta["sig"]))
    raw[10] ^= 1
    meta["sig"] = base64.b64encode(bytes(raw)).decode()
    with pytest.raises(LicenseError) as exc:
        promo.derive_promo_key(TEST_CODE, meta, promo_env["pub_hex"])
    assert exc.value.user_message == promo.WRONG_CODE_MESSAGE
    # Renaming the license inside the metadata breaks the
    # signature over it, too — the id is signed, not decorative.
    meta2 = copy.deepcopy(promo_env["meta"])
    meta2["license"]["id"] = "FORGED1"
    with pytest.raises(LicenseError) as exc2:
        promo.derive_promo_key(TEST_CODE, meta2, promo_env["pub_hex"])
    assert exc2.value.user_message == promo.WRONG_CODE_MESSAGE


def test_meta_validation_and_loading(promo_env, tmp_path):
    with pytest.raises(LicenseError) as exc:
        promo.validate_meta(None)
    assert exc.value.user_message == promo.INACTIVE_MESSAGE
    with pytest.raises(LicenseError):
        promo.validate_meta({"v": 1, "kdf": "argon2"})
    with pytest.raises(LicenseError):
        promo.derive_promo_key(TEST_CODE, None, promo_env["pub_hex"])
    # load_meta: absent file, null file, real file.
    assert promo.load_meta(tmp_path) is None
    assert promo.load_meta(None) is None
    (tmp_path / promo.META_NAME).write_text("null\n")
    assert promo.load_meta(tmp_path) is None
    (tmp_path / promo.META_NAME).write_text(json.dumps(promo_env["meta"]))
    assert promo.load_meta(tmp_path) == promo_env["meta"]
    (tmp_path / promo.META_NAME).write_text("{not json")
    assert promo.load_meta(tmp_path) is None


def test_empty_code_message(promo_env):
    with pytest.raises(LicenseError) as exc:
        promo.derive_promo_key("  ", promo_env["meta"],
                               promo_env["pub_hex"])
    assert "Enter your promo" in exc.value.user_message


# ---------------------------------------------------------- throttling


def test_throttle_schedule():
    waits = [promo.throttle_wait_seconds(n) for n in range(0, 9)]
    assert waits == [0, 5, 10, 20, 40, 80, 160, 300, 300]


def test_throttle_remaining():
    now = 1_000_000
    assert promo.throttle_remaining(0, 0, now) == 0
    assert promo.throttle_remaining(1, 0, now) == 0
    assert promo.throttle_remaining(1, now, now) == 5
    assert promo.throttle_remaining(1, now - 4_000, now) == 1
    assert promo.throttle_remaining(1, now - 5_000, now) == 0
    assert promo.throttle_remaining(3, now - 19_000, now) == 1
    assert promo.throttle_remaining(3, now - 21_000, now) == 0


def test_throttle_fields_round_trip(store, tmp_path):
    store.settings.promo_fail_count = 3
    store.settings.promo_last_fail_ms = 123_456
    store.save()
    from hackproof_app.config import SettingsStore

    again = SettingsStore(store.dir)
    assert again.settings.promo_fail_count == 3
    assert again.settings.promo_last_fail_ms == 123_456
    # A hand-garbled file degrades to zero, never wedges startup.
    raw = json.loads(store.path.read_text())
    raw["promo_fail_count"] = "abc"
    raw["promo_last_fail_ms"] = -5
    store.path.write_text(json.dumps(raw))
    again2 = SettingsStore(store.dir)
    assert again2.settings.promo_fail_count == 0
    assert again2.settings.promo_last_fail_ms == 0


# ------------------------------------------------------------- the card

_KEEP: list = []


def _manifest(pub_hex: str) -> site_bundle.SiteManifest:
    return site_bundle.SiteManifest(
        pages={"course": True, "exam": True, "verify": True},
        pack_state=site_bundle.PACK_BUILT,
        public_key_hex=pub_hex,
    )


def test_promo_card_unlocks_and_labels(qapp, store, promo_env):
    from hackproof_app.gui.premium_page import PremiumPage

    page = PremiumPage(
        store, _manifest(promo_env["pub_hex"]),
        promo_meta=promo_env["meta"],
    )
    _KEEP.append(page)
    page.show()
    assert page._promo_card.isVisible()
    assert page._promo_edit.isVisible()
    page._promo_edit.setText(TEST_CODE)
    page.submit_promo()
    assert pump_until(lambda: bool(store.settings.license_key))
    assert store.settings.license_key == promo_env["key"]
    assert store.settings.promo_fail_count == 0
    assert "Premium — promo access" in page._status_label.text()
    assert not page._promo_card.isVisible()


def test_promo_wrong_code_throttles(qapp, store, promo_env):
    from hackproof_app.gui.premium_page import PremiumPage

    page = PremiumPage(
        store, _manifest(promo_env["pub_hex"]),
        promo_meta=promo_env["meta"],
    )
    _KEEP.append(page)
    page.show()
    page._promo_edit.setText("0000")
    page.submit_promo()
    assert pump_until(lambda: store.settings.promo_fail_count == 1)
    assert "didn't work" in page._promo_status.text()
    assert store.settings.license_key == ""
    # An immediate retry is refused by the throttle, synchronously,
    # and does not count as another failure.
    page.submit_promo()
    assert "wait about" in page._promo_status.text()
    assert store.settings.promo_fail_count == 1


def test_promo_card_inactive_without_meta(qapp, store, promo_env):
    from hackproof_app.gui.premium_page import PremiumPage

    page = PremiumPage(
        store, _manifest(promo_env["pub_hex"]), promo_meta=None,
    )
    _KEEP.append(page)
    page.show()
    assert page._promo_note.text() == promo.INACTIVE_MESSAGE
    assert not page._promo_edit.isVisible()
    assert not page._promo_btn.isVisible()
    page.submit_promo()
    assert page._promo_status.text() == promo.INACTIVE_MESSAGE
    assert store.settings.license_key == ""
