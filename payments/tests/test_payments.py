"""HackProof payment service test suite — no live network, no real
money, throwaway keys only.

Run:  python3 -m unittest discover -s payments/tests -v
(or pytest payments/tests). Needs `cryptography` (same dependency as
tools/keygen.py).

Coverage:
  * service-minted keys are accepted by the REAL tools/keygen.py
    (license_secret_from_key) and keygen-minted keys by the service —
    byte-compatible minting, proven both directions;
  * certificate validation equivalence: for every case in the matrix,
    the service and keygen.py's own sign-cert make the SAME accept /
    refuse decision, and on acceptance their countersigned output is
    byte-identical;
  * watcher: detection, exact-amount matching, 0-conf no-mint,
    1-conf mints exactly once, restart idempotency, expiry, wrong
    amount, double payment;
  * certificates endpoint behaviour: clean issues + emails once,
    flagged held (never sent), duplicates idempotent.
"""

from __future__ import annotations

import base64
import contextlib
import copy
import hashlib
import hmac as hmac_mod
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest

PAYMENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PAYMENTS_DIR)
sys.path.insert(0, PAYMENTS_DIR)

from hackproof_pay import crypto_core  # noqa: E402
from hackproof_pay.chain import confirmations  # noqa: E402
from hackproof_pay.certsvc import (CertificateError,  # noqa: E402
                                   CertificateService, integrity_verdict)
from hackproof_pay.config import DEFAULTS, Config  # noqa: E402
from hackproof_pay.httpd import App  # noqa: E402
from hackproof_pay.mailer import Mailer  # noqa: E402
from hackproof_pay.pricing import (Pricer, allocate_total,  # noqa: E402
                                   sats_to_btc_str)
from hackproof_pay.store import Store  # noqa: E402

# --- load the REAL seller tool for equivalence testing ---------------
_spec = importlib.util.spec_from_file_location(
    "keygen", os.path.join(REPO_ROOT, "tools", "keygen.py"))
keygen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(keygen)


# ----------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------

def write_keystore(keydir):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    os.makedirs(keydir, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    seed = priv.private_bytes(serialization.Encoding.Raw,
                              serialization.PrivateFormat.Raw,
                              serialization.NoEncryption())
    pub = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    for name, data, mode in (
            ("ed25519-private.key", seed, 0o600),
            ("ed25519-public.key", pub, 0o644),
            ("content-master.key", os.urandom(32), 0o600)):
        p = os.path.join(keydir, name)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(fd, "wb") as f:
            f.write(data)


class FakeChain:
    def __init__(self):
        self.tip = 800_000
        self.txs = []

    def tip_height(self):
        return self.tip

    def address_txs(self, address):
        return list(self.txs)


class CaptureMailer(Mailer):
    def __init__(self):
        super().__init__({}, "owner@example.com")
        self.sent = []

    @property
    def configured(self):
        return True

    def send(self, to, subject, body, attachments=()):
        self.sent.append({"to": to, "subject": subject, "body": body,
                          "attachments": list(attachments)})
        return True


def pay_tx(txid, address, sats, confs, tip):
    return {"txid": txid,
            "vout": [{"scriptpubkey_address": address, "value": sats}],
            "status": {"confirmed": confs > 0,
                       "block_height": (tip - confs + 1)
                       if confs else None}}


class ServiceFixture(unittest.TestCase):
    RATE = 50000.0           # $50,000/BTC  ->  base = 10,000 sats
    BASE_SATS = 10000

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hackproof-test-")
        self.keydir = os.path.join(self.tmp, "keys")
        write_keystore(self.keydir)
        self.keys = crypto_core.load_keystore(self.keydir)
        values = copy.deepcopy(DEFAULTS)
        values.update({
            "keydir": self.keydir,
            "data_dir": os.path.join(self.tmp, "data"),
            "admin_token": "test-admin-token",
        })
        self.cfg = Config(values)
        self.store = Store(self.cfg.db_path)
        body = json.dumps({"bitcoin": {"usd": self.RATE}})
        self.pricer = Pricer(
            self.cfg["coingecko_url"], self.cfg["price_usd"],
            fetcher=lambda url: (200, body), cache_seconds=3600)
        self.chain = FakeChain()
        self.mailer = CaptureMailer()
        self.app = App(self.cfg, self.store, self.keys, self.mailer,
                       self.pricer, self.chain)
        self.address = self.cfg["btc_address"]

    def tearDown(self):
        self.store.close()

    def create_order(self, email="buyer@example.com"):
        return self.app.orders.create_order(email)

    def mint_genuine_license(self):
        license_key, lic = crypto_core.mint_license(self.keys, days=365)
        _, S = crypto_core.parse_and_verify_license(self.keys,
                                                    license_key)
        return license_key, lic, S


# ----------------------------------------------------------------------
# pricing primitives
# ----------------------------------------------------------------------

class TestPricing(unittest.TestCase):
    def test_base_sats_integer_math(self):
        p = Pricer("http://x", 5.00, fetcher=None)
        self.assertEqual(p.base_sats(50000.0), 10000)
        self.assertEqual(p.base_sats(100000.0), 5000)

    def test_sats_to_btc_str(self):
        self.assertEqual(sats_to_btc_str(10001), "0.00010001")
        self.assertEqual(sats_to_btc_str(100_000_000), "1.00000000")
        self.assertEqual(sats_to_btc_str(1), "0.00000001")

    def test_allocate_unique_and_exhaustion(self):
        total, off = allocate_total(10000, {10001, 10002}, 999)
        self.assertEqual((total, off), (10003, 3))
        with self.assertRaises(Exception):
            allocate_total(10000, {10001, 10002, 10003}, 3)

    def test_confirmations_math(self):
        tx = {"status": {"confirmed": False}}
        self.assertEqual(confirmations(tx, 800000), 0)
        tx = {"status": {"confirmed": True, "block_height": 799999}}
        self.assertEqual(confirmations(tx, 800000), 2)


# ----------------------------------------------------------------------
# minting equivalence with the real keygen.py
# ----------------------------------------------------------------------

class TestMintEquivalence(ServiceFixture):
    def test_keygen_accepts_service_minted_key(self):
        license_key, lic = crypto_core.mint_license(self.keys, days=365)
        pubkey_obj = self.keys._priv.public_key()
        S, lic_id = keygen.license_secret_from_key(pubkey_obj,
                                                   license_key)
        self.assertEqual(lic_id, lic["id"])
        _, S2 = crypto_core.parse_and_verify_license(self.keys,
                                                     license_key)
        self.assertEqual(S, S2)
        self.assertEqual(len(S), 32)

    def test_service_accepts_keygen_minted_key(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            keygen.cmd_mint(self.keydir, "premium", 365)
        lines = buf.getvalue().splitlines()
        license_key = lines[1].strip()
        lic, S = crypto_core.parse_and_verify_license(self.keys,
                                                      license_key)
        self.assertEqual(lic["tier"], "premium")
        self.assertEqual(len(S), 32)

    def test_both_mints_unwrap_the_real_content_key(self):
        for make in (
                lambda: crypto_core.mint_license(self.keys, days=365)[0],
        ):
            lic, _ = crypto_core.parse_and_verify_license(
                self.keys, make())
            self.assertEqual(
                crypto_core.unwrap_content_key(None, lic),
                self.keys.content_key)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            keygen.cmd_mint(self.keydir, "premium", 365)
        kg_key = buf.getvalue().splitlines()[1].strip()
        lic, _ = crypto_core.parse_and_verify_license(self.keys, kg_key)
        self.assertEqual(crypto_core.unwrap_content_key(None, lic),
                         self.keys.content_key)

    def test_mint_days_validation_matches_keygen(self):
        for days in (0, -1, 3651):
            with self.assertRaises(Exception):
                crypto_core.mint_license(self.keys, days=days)
            with self.assertRaises(SystemExit):
                with contextlib.redirect_stdout(io.StringIO()):
                    keygen.cmd_mint(self.keydir, "premium", days)

    def test_tampered_key_rejected_by_both(self):
        license_key, lic = crypto_core.mint_license(self.keys, days=365)
        raw = json.loads(base64.b64decode(license_key))
        raw["expiry"] += 10 * 365 * 86400  # extend without re-signing
        forged = base64.b64encode(json.dumps(
            raw, separators=(",", ":")).encode()).decode()
        with self.assertRaises(crypto_core.LicenseError):
            crypto_core.parse_and_verify_license(self.keys, forged)
        with self.assertRaises(SystemExit):
            keygen.license_secret_from_key(self.keys._priv.public_key(),
                                           forged)


# ----------------------------------------------------------------------
# watcher / payments
# ----------------------------------------------------------------------

class TestWatcher(ServiceFixture):
    def test_two_open_orders_get_unique_amounts(self):
        o1 = self.create_order("a@example.com")
        o2 = self.create_order("b@example.com")
        self.assertNotEqual(o1["btc_amount_sats"], o2["btc_amount_sats"])
        self.assertEqual(o1["btc_amount_sats"] - self.BASE_SATS, 1)
        self.assertEqual(o2["btc_amount_sats"] - self.BASE_SATS, 2)

    def test_zero_conf_stays_confirming_no_mint(self):
        o = self.create_order()
        self.chain.txs = [pay_tx("aa" * 32, self.address,
                                 o["btc_amount_sats"], 0, self.chain.tip)]
        self.app.watcher.poll_once()
        got = self.app.orders.get_order(o["order_id"])
        self.assertEqual(got["status"], "confirming")
        self.assertNotIn("license_key", got)
        self.assertEqual(self.mailer.sent, [])

    def test_one_conf_mints_exactly_once_and_emails(self):
        o = self.create_order()
        tx = lambda c: pay_tx("bb" * 32, self.address,
                              o["btc_amount_sats"], c, self.chain.tip)
        self.chain.txs = [tx(0)]
        self.app.watcher.poll_once()
        self.chain.txs = [tx(1)]
        self.app.watcher.poll_once()
        self.app.watcher.poll_once()  # extra polls must not re-mint
        self.app.watcher.poll_once()
        got = self.app.orders.get_order(o["order_id"])
        self.assertEqual(got["status"], "paid")
        lic, _ = crypto_core.parse_and_verify_license(
            self.keys, got["license_key"])
        self.assertEqual(
            crypto_core.unwrap_content_key(None, lic),
            self.keys.content_key)
        key_mails = [m for m in self.mailer.sent
                     if "license key" in m["subject"]]
        self.assertEqual(len(key_mails), 1)
        self.assertIn(got["license_key"], key_mails[0]["body"])
        self.assertIn("THIS KEY IS YOUR ACCOUNT", key_mails[0]["body"])

    def test_restart_idempotency_no_second_mint(self):
        o = self.create_order()
        self.chain.txs = [pay_tx("cc" * 32, self.address,
                                 o["btc_amount_sats"], 3, self.chain.tip)]
        self.app.watcher.poll_once()
        key1 = self.app.orders.get_order(o["order_id"])["license_key"]
        # simulate a restart: fresh Store + App over the same DB file
        self.store.close()
        store2 = Store(self.cfg.db_path)
        mailer2 = CaptureMailer()
        app2 = App(self.cfg, store2, self.keys, mailer2, self.pricer,
                   self.chain)
        app2.watcher.poll_once()
        app2.watcher.poll_once()
        key2 = app2.orders.get_order(o["order_id"])["license_key"]
        self.assertEqual(key1, key2)
        self.assertEqual(mailer2.sent, [])
        store2.close()
        self.store = Store(self.cfg.db_path)  # for tearDown

    def test_wrong_amount_never_mints(self):
        o = self.create_order()
        self.chain.txs = [pay_tx("dd" * 32, self.address,
                                 self.BASE_SATS + 500, 5, self.chain.tip)]
        self.app.watcher.poll_once()
        got = self.app.orders.get_order(o["order_id"])
        self.assertEqual(got["status"], "awaiting_payment")
        events = self.store.list_events()
        self.assertTrue(any(e["kind"] == "unmatched" for e in events))
        self.assertEqual(self.mailer.sent, [])

    def test_expired_order_does_not_mint_late_payment(self):
        o = self.create_order()
        # force the window shut
        with self.store._lock, self.store._conn:
            self.store._conn.execute(
                "UPDATE orders SET expires_at=1 WHERE order_id=?",
                (o["order_id"],))
        self.chain.txs = [pay_tx("ee" * 32, self.address,
                                 o["btc_amount_sats"], 2, self.chain.tip)]
        self.app.watcher.poll_once()
        got = self.app.orders.get_order(o["order_id"])
        self.assertEqual(got["status"], "expired")
        self.assertNotIn("license_key", got)
        events = self.store.list_events()
        self.assertTrue(any(e["kind"] == "late" for e in events))

    def test_second_payment_after_paid_is_duplicate_event(self):
        o = self.create_order()
        self.chain.txs = [pay_tx("f1" * 32, self.address,
                                 o["btc_amount_sats"], 1, self.chain.tip)]
        self.app.watcher.poll_once()
        key = self.app.orders.get_order(o["order_id"])["license_key"]
        self.chain.txs.append(pay_tx("f2" * 32, self.address,
                                     o["btc_amount_sats"], 1,
                                     self.chain.tip))
        self.app.watcher.poll_once()
        got = self.app.orders.get_order(o["order_id"])
        self.assertEqual(got["license_key"], key)  # unchanged
        events = self.store.list_events()
        self.assertTrue(any(e["kind"] == "duplicate" for e in events))
        key_mails = [m for m in self.mailer.sent
                     if "license key" in m["subject"]]
        self.assertEqual(len(key_mails), 1)

    def test_bad_email_rejected(self):
        with self.assertRaises(Exception):
            self.create_order("not-an-email")


# ----------------------------------------------------------------------
# certificate validation equivalence + endpoint behaviour
# ----------------------------------------------------------------------

def expected_pct(score):
    return (score * 200 + 90) // 180


def make_payload(S, lic_id, score=81, name="Test Student",
                 cert_id="HP-TST-001", date="2026-10-19", pct=None,
                 with_proof=True, tamper_name=False):
    payload = {"v": 1, "cert_id": cert_id, "name": name,
               "score": score,
               "pct": expected_pct(score) if pct is None else pct,
               "date": date, "lic_id": lic_id}
    if with_proof:
        canonical = json.dumps(payload, separators=(",", ":"),
                               ensure_ascii=False).encode()
        payload["proof"] = base64.b64encode(
            hmac_mod.new(S, canonical, hashlib.sha256).digest()).decode()
    if tamper_name:
        payload["name"] = "Mallory Forgery"
    code = base64.b64encode(
        json.dumps(payload, separators=(",", ":"),
                   ensure_ascii=False).encode()).decode()
    return payload, code


def keygen_sign_cert(keydir, code, license_key):
    """Drive the real keygen sign-cert. Returns ('ok', output_code) or
    ('refused', message)."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            keygen.cmd_sign_cert(keydir, code, license_key)
    except SystemExit as exc:
        return "refused", str(exc.code)
    lines = buf.getvalue().splitlines()
    return "ok", lines[1].strip()


class TestCertificates(ServiceFixture):
    def setUp(self):
        super().setUp()
        self.license_key, self.lic, self.S = self.mint_genuine_license()
        self.certs = CertificateService(self.cfg, self.store, self.keys,
                                        self.mailer)

    def submit(self, code, license_key=None, integrity="clean",
               email="student@example.com"):
        body = {"certificate_code": code,
                "license_key": license_key or self.license_key,
                "email": email,
                "integrity": {"verdict": integrity}}
        try:
            status, resp = self.certs.submit(body)
            return status, resp
        except CertificateError as exc:
            return exc.status, {"error": str(exc)}

    def test_genuine_clean_issues_and_countersign_matches_keygen(self):
        payload, code = make_payload(self.S, self.lic["id"])
        kg_status, kg_out = keygen_sign_cert(self.keydir, code,
                                             self.license_key)
        self.assertEqual(kg_status, "ok")
        status, resp = self.submit(code)
        self.assertEqual(status, 201)
        self.assertEqual(resp["status"], "issued")
        # byte-identical countersigning vs the manual tool
        self.assertEqual(resp["countersigned_code"], kg_out)
        verified = crypto_core.verify_countersigned(
            self.keys.pub_bytes, resp["countersigned_code"])
        self.assertEqual(verified["cert_id"], "HP-TST-001")
        cert_mails = [m for m in self.mailer.sent
                      if "Certificate" in m["subject"]]
        self.assertEqual(len(cert_mails), 1)
        self.assertIn("Sentinel Safeguard Certificate of Cyber "
                      "Security Awareness Course Completion",
                      cert_mails[0]["body"])
        self.assertEqual(len(cert_mails[0]["attachments"]), 1)
        fname, data, mt, st = cert_mails[0]["attachments"][0]
        self.assertIn("HP-TST-001", fname)
        self.assertIn(b"Test Student", data)

    def test_duplicate_submission_idempotent(self):
        payload, code = make_payload(self.S, self.lic["id"])
        s1, r1 = self.submit(code)
        s2, r2 = self.submit(code)
        self.assertEqual(s1, 201)
        self.assertEqual(s2, 200)
        self.assertEqual(r1["countersigned_code"],
                         r2["countersigned_code"])
        cert_mails = [m for m in self.mailer.sent
                      if "Certificate" in m["subject"]]
        self.assertEqual(len(cert_mails), 1)

    def test_flagged_is_held_never_sent(self):
        payload, code = make_payload(self.S, self.lic["id"])
        status, resp = self.submit(code, integrity="flagged")
        self.assertEqual(status, 202)
        self.assertEqual(resp["status"], "held_for_review")
        self.assertEqual(self.mailer.sent, [])
        held = self.store.list_review()
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["cert_id"], "HP-TST-001")
        # resubmission stays a single queue entry
        self.submit(code, integrity="flagged")
        self.assertEqual(len(self.store.list_review()), 1)

    def test_missing_integrity_block_fails_closed_to_hold(self):
        payload, code = make_payload(self.S, self.lic["id"])
        body = {"certificate_code": code,
                "license_key": self.license_key,
                "email": "student@example.com"}
        status, resp = self.certs.submit(body)
        self.assertEqual(status, 202)

    def test_equivalence_matrix(self):
        other_key, other_lic, other_S = self.mint_genuine_license()
        _, code_71 = make_payload(self.S, self.lic["id"], score=71)
        #   ^ proof is genuine — for a FAILING score (71/79)
        _, code_100 = make_payload(self.S, self.lic["id"], score=100,
                                   pct=100)
        _, code_badpct = make_payload(self.S, self.lic["id"], score=85,
                                      pct=93)
        _, code_wronglic = make_payload(self.S, self.lic["id"])
        _, code_tampered = make_payload(self.S, self.lic["id"],
                                        tamper_name=True)
        _, code_noproof = make_payload(self.S, self.lic["id"],
                                       with_proof=False)
        signed_payload, _ = make_payload(self.S, self.lic["id"])
        signed_payload["sig"] = "AAAA"
        code_signed = base64.b64encode(json.dumps(
            signed_payload, separators=(",", ":"),
            ensure_ascii=False).encode()).decode()

        cases = [
            ("failing 71/79 waved through", code_71, self.license_key),
            ("impossible 100/90", code_100, self.license_key),
            ("mismatched percentage", code_badpct, self.license_key),
            ("wrong license for payload", code_wronglic, other_key),
            ("tampered name (bad HMAC)", code_tampered,
             self.license_key),
            ("missing HMAC proof", code_noproof, self.license_key),
            ("already-signed payload", code_signed, self.license_key),
        ]
        for name, code, lic_key in cases:
            with self.subTest(case=name):
                kg_status, _ = keygen_sign_cert(self.keydir, code,
                                                lic_key)
                self.assertEqual(kg_status, "refused",
                                 "keygen must refuse: %s" % name)
                status, resp = self.submit(code, license_key=lic_key)
                self.assertEqual(status, 400,
                                 "service must refuse: %s" % name)
                self.assertEqual(self.mailer.sent, [])

    def test_genuine_at_boundary_scores(self):
        for score in (72, 90):
            with self.subTest(score=score):
                payload, code = make_payload(
                    self.S, self.lic["id"], score=score,
                    cert_id="HP-TST-%03d" % score)
                kg_status, kg_out = keygen_sign_cert(
                    self.keydir, code, self.license_key)
                self.assertEqual(kg_status, "ok")
                status, resp = self.submit(code)
                self.assertEqual(status, 201)
                self.assertEqual(resp["countersigned_code"], kg_out)

    def test_integrity_verdict_parsing(self):
        self.assertEqual(integrity_verdict({"verdict": "clean"}),
                         "clean")
        self.assertEqual(integrity_verdict({"verdict": "flagged"}),
                         "flagged")
        self.assertEqual(integrity_verdict({"clean": True}), "clean")
        self.assertEqual(integrity_verdict({}), "flagged")
        self.assertEqual(integrity_verdict(None), "flagged")
        self.assertEqual(integrity_verdict({"verdict": "weird"}),
                         "flagged")


if __name__ == "__main__":
    unittest.main()
