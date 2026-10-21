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
from hackproof_pay.httpd import App, make_server  # noqa: E402
from hackproof_pay.mailer import Mailer  # noqa: E402
from hackproof_pay.pricing import (Pricer, PricingError,  # noqa: E402
                                   allocate_total, sats_to_btc_str)
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
    # keygen prints an INTEGRITY line first, then the banner, then
    # the code — locate the code relative to the banner instead of
    # assuming a fixed line number (the integrity print landed
    # after these tests were written and silently shifted it).
    banner = next(i for i, line in enumerate(lines)
                  if line.startswith("COUNTERSIGNED CERTIFICATE"))
    return "ok", lines[banner + 1].strip()


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


class TestSweep2Regressions(ServiceFixture):
    """Bug-hunt sweep #2 (2026-10-19): concurrency + HTTP edge cases."""

    def test_concurrent_create_order_totals_stay_unique(self):
        # Slow the reserved-totals read down so concurrent creators
        # overlap inside the reserve-allocate-insert sequence; the
        # totals are the payment-matching key and must never repeat
        # among open orders.
        import threading
        import time as _time
        orig = self.store.open_totals

        def slow(now):
            reserved = orig(now)
            _time.sleep(0.02)
            return reserved

        self.store.open_totals = slow
        barrier = threading.Barrier(6)
        results, errors = [], []

        def worker(i):
            barrier.wait()
            try:
                results.append(
                    self.app.orders.create_order("u%d@x.co" % i))
            except Exception as exc:  # noqa: BLE001 - recorded below
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,))
                   for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        totals = [r["btc_amount_sats"] for r in results]
        self.assertEqual(len(set(totals)), len(totals))

    def test_pricer_network_failure_is_pricing_error(self):
        import urllib.error

        def boom(url):
            raise urllib.error.URLError("dns exploded")

        pricer = Pricer("https://price.invalid", 5.0, fetcher=boom)
        with self.assertRaises(PricingError):
            pricer.btc_rate_usd()

    def test_cert_email_header_injection_refused(self):
        license_key, lic, S = self.mint_genuine_license()
        _, code = make_payload(S, lic["id"])
        certs = CertificateService(self.cfg, self.store, self.keys,
                                   self.mailer)
        body = {"certificate_code": code, "license_key": license_key,
                "email": "victim@example.com\r\nBcc: evil@example.com",
                "integrity": {"verdict": "clean"}}
        with self.assertRaises(CertificateError):
            certs.submit(body)
        self.assertEqual(self.mailer.sent, [])

    def test_mailer_bad_address_degrades_to_not_sent(self):
        mailer = Mailer(
            {"host": "127.0.0.1", "port": 9, "security": "none",
             "from_address": "a@b.co"}, "s@x.co")
        self.assertFalse(mailer.send(
            "victim@example.com\r\nBcc: evil@example.com", "hi",
            "body"))

    def test_admin_token_non_ascii_gets_401_not_500(self):
        import socket
        import threading
        server = make_server(self.app, "127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever,
                                  daemon=True)
        thread.start()
        try:
            with socket.create_connection(("127.0.0.1", port),
                                          timeout=5) as sock:
                sock.sendall(
                    b"GET /api/admin/review HTTP/1.1\r\nHost: x\r\n"
                    b"X-Admin-Token: s\xe9kret\r\n"
                    b"Connection: close\r\n\r\n")
                response = sock.recv(4096)
        finally:
            server.shutdown()
        self.assertIn(b" 401 ", response.split(b"\r\n")[0])


class TestSweep3Regressions(ServiceFixture):
    """Bug-hunt sweep #3 (2026-10-21): emailed-certificate palette,
    delivered-flag truthfulness, non-object POST bodies."""

    def test_emailed_certificate_contrast_audit(self):
        # Every text/background pairing in the rendered emailed
        # certificate must measure >= 4.5:1 (WCAG AA), computed
        # from the shipped values — against the DARKER cream stop
        # (#f5efe4), the worst case for text on the stock.
        import re

        from hackproof_pay.certgen import render_certificate_html

        html = render_certificate_html(
            {"name": "Test Student", "pct": 90, "score": 81,
             "date": "2026-10-21", "cert_id": "HP-TST-001"},
            "https://example.invalid/verify.html")

        def lum(hex6):
            if len(hex6) == 4:  # #fff -> #ffffff
                hex6 = "#" + "".join(c * 2 for c in hex6[1:])
            r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (1, 3, 5))
            f = lambda c: (c / 12.92 if c <= 0.04045
                           else ((c + 0.055) / 1.055) ** 2.4)
            return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

        def ratio(a, b):
            la, lb = lum(a), lum(b)
            return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

        def rule_color(selector):
            m = re.search(re.escape(selector) + r"\{[^}]*?color:"
                          r"(#[0-9a-fA-F]{6})", html)
            self.assertIsNotNone(m, selector)
            return m.group(1).lower()

        cream = "#f5efe4"       # darker gradient stop = worst case
        ground = "#050807"      # the page ground behind .verify-note
        # Text on the cream stock.
        for sel in (".cert .org", ".cert .sub", ".cert .label",
                    ".cert .details", ".cert .cid", ".cert .sig"):
            self.assertGreaterEqual(ratio(rule_color(sel), cream),
                                    4.5, sel)
        self.assertGreaterEqual(ratio(rule_color(".cert"), cream),
                                4.5, ".cert base text")
        self.assertGreaterEqual(ratio(rule_color(".cert h3"), cream),
                                4.5, ".cert h3")
        self.assertGreaterEqual(ratio(rule_color(".cert .name"),
                                      cream), 4.5, ".cert .name")
        # The badge: white text on its fill.
        badge = re.search(r"\.cert \.badge\{([^}]*)\}", html, re.S)
        self.assertIsNotNone(badge)
        bg = re.search(r"background:(#[0-9a-fA-F]{3,6})",
                       badge.group(1)).group(1)
        fg = re.search(r"color:(#[0-9a-fA-F]{3,6})",
                       badge.group(1)).group(1)
        self.assertGreaterEqual(ratio(fg, bg), 4.5, "badge text")
        # The verify note sits on the dark page ground.
        self.assertGreaterEqual(ratio(rule_color(".verify-note"),
                                      ground), 4.5, ".verify-note")
        self.assertGreaterEqual(ratio(rule_color(".verify-note b"),
                                      ground), 4.5, ".verify-note b")
        # The academy precedents from app-v1.0.4, on the light stop:
        # DEEP 8.44:1 for accents, small-print tone 12.81:1.
        self.assertAlmostEqual(ratio("#115635", "#fdfbf7"), 8.44,
                               places=2)
        self.assertAlmostEqual(ratio("#0c3723", "#fdfbf7"), 12.81,
                               places=2)
        self.assertEqual(rule_color(".cert .org"), "#115635")
        self.assertEqual(rule_color(".cert .label"), "#0c3723")
        # Certificate gold never carries text on the cream stock
        # (it measures 2.34:1 there): its only text use in this
        # file is the verify note's emphasis on the dark ground.
        self.assertLess(ratio("#c9a227", "#fdfbf7"), 4.5)
        cert_block = html.split(".verify-note")[0]
        self.assertNotIn("#c9a227", cert_block)
        # The retired house-green text tokens and any purple are
        # gone from the emailed certificate.
        for tok in ("#14532d", "#2f4536", "#1e7a3c", "#9db3a4",
                    "#8fd6a4"):
            self.assertNotIn(tok, html)

    def test_issued_response_reports_delivery_truthfully(self):
        license_key, lic, S = self.mint_genuine_license()
        _, code = make_payload(S, lic["id"])
        certs = CertificateService(self.cfg, self.store, self.keys,
                                   self.mailer)
        status, resp = certs.submit(
            {"certificate_code": code, "license_key": license_key,
             "email": "student@example.com",
             "integrity": {"verdict": "clean"}})
        self.assertEqual(status, 201)
        # The capture mailer DID send it — the response must say so.
        self.assertTrue(resp["delivered"])
        self.assertTrue(self.store.get_certificate(
            lic["id"], "HP-TST-001")["delivered"])
        # Resubmission reports the same truth.
        status2, resp2 = certs.submit(
            {"certificate_code": code, "license_key": license_key,
             "email": "student@example.com",
             "integrity": {"verdict": "clean"}})
        self.assertEqual(status2, 200)
        self.assertTrue(resp2["delivered"])

    def test_non_object_post_body_gets_400_not_500(self):
        import socket
        import threading
        server = make_server(self.app, "127.0.0.1", 0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever,
                                  daemon=True)
        thread.start()
        try:
            with socket.create_connection(("127.0.0.1", port),
                                          timeout=5) as sock:
                sock.sendall(
                    b"POST /api/admin/review/1/resolve HTTP/1.1\r\n"
                    b"Host: x\r\nX-Admin-Token: test-admin-token\r\n"
                    b"Content-Type: application/json\r\n"
                    b"Content-Length: 5\r\nConnection: close\r\n\r\n"
                    b"[1,2]")
                response = sock.recv(4096)
        finally:
            server.shutdown()
        self.assertIn(b" 400 ", response.split(b"\r\n")[0])


if __name__ == "__main__":
    unittest.main()
