"""Persistent store (SQLite, stdlib) — the service's memory.

Lives on the host only (default ~/.hackproof-payments/). Holds orders,
issued certificates, the certificate review queue, and a payment-event
log for payments that need the owner's eyes (wrong amount, late,
duplicate, unmatched). All writes go through transactions; the minting
claim is a conditional UPDATE so an order can never mint twice — not
across double polls, not across restarts.

The store contains license keys (they are bearer credentials — the key
IS the account) and, in the review queue, the license keys students
submitted with held certificates (needed so the owner can run the
manual sign-cert tool). Protect the file like the product it unlocks:
mode 600 where the OS supports it, host accounts only.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id      TEXT PRIMARY KEY,
    email         TEXT NOT NULL,
    price_usd     REAL NOT NULL,
    rate_usd      REAL NOT NULL,
    base_sats     INTEGER NOT NULL,
    offset_sats   INTEGER NOT NULL,
    total_sats    INTEGER NOT NULL,
    btc_address   TEXT NOT NULL,
    status        TEXT NOT NULL,  -- awaiting_payment|confirming|paid|expired
    txid          TEXT,
    confirmations INTEGER NOT NULL DEFAULT 0,
    created_at    INTEGER NOT NULL,
    expires_at    INTEGER NOT NULL,
    paid_at       INTEGER,
    license_key   TEXT,
    license_id    TEXT,
    delivery      TEXT,           -- sent|claim_only|failed
    delivery_note TEXT
);
CREATE TABLE IF NOT EXISTS seen_payments (
    payment_ref TEXT PRIMARY KEY,  -- "<txid>:<vout_index>"
    txid        TEXT NOT NULL,
    amount_sats INTEGER NOT NULL,
    seen_at     INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS payment_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    kind        TEXT NOT NULL,  -- unmatched|wrong_amount|late|duplicate|tx_vanished
    order_id    TEXT,
    txid        TEXT,
    amount_sats INTEGER,
    detail      TEXT
);
CREATE TABLE IF NOT EXISTS certificates (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    lic_id             TEXT NOT NULL,
    cert_id            TEXT NOT NULL,
    email              TEXT NOT NULL,
    name               TEXT NOT NULL,
    score              INTEGER NOT NULL,
    pct                INTEGER NOT NULL,
    cert_date          TEXT,
    payload_json       TEXT NOT NULL,
    countersigned_code TEXT NOT NULL,
    cert_html          TEXT NOT NULL,
    delivered          INTEGER NOT NULL DEFAULT 0,
    created_at         INTEGER NOT NULL,
    UNIQUE(lic_id, cert_id)
);
CREATE TABLE IF NOT EXISTS review_queue (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    lic_id        TEXT,
    cert_id       TEXT,
    email         TEXT NOT NULL,
    name          TEXT,
    score         INTEGER,
    pct           INTEGER,
    payload_json  TEXT NOT NULL,
    license_key   TEXT NOT NULL,
    integrity_json TEXT,
    status        TEXT NOT NULL DEFAULT 'held',  -- held|resolved|dismissed
    received_at   INTEGER NOT NULL,
    UNIQUE(lic_id, cert_id)
);
"""


class Store:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()
        try:
            os.chmod(db_path, 0o600)
        except OSError:
            pass  # Windows: rely on the user profile's ACLs (documented)

    def close(self):
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------- orders

    def create_order(self, order):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO orders(order_id,email,price_usd,rate_usd,"
                "base_sats,offset_sats,total_sats,btc_address,status,"
                "created_at,expires_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (order["order_id"], order["email"], order["price_usd"],
                 order["rate_usd"], order["base_sats"],
                 order["offset_sats"], order["total_sats"],
                 order["btc_address"], "awaiting_payment",
                 order["created_at"], order["expires_at"]))

    def get_order(self, order_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM orders WHERE order_id=?",
                (order_id,)).fetchone()
        return dict(row) if row else None

    def open_orders(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM orders WHERE status IN "
                "('awaiting_payment','confirming')").fetchall()
        return [dict(r) for r in rows]

    def open_totals(self, now):
        """Total-sats amounts currently reserved by live open orders."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT total_sats FROM orders WHERE status IN "
                "('awaiting_payment','confirming') AND expires_at>?",
                (now,)).fetchall()
        return {r["total_sats"] for r in rows}

    def expire_order(self, order_id, now):
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE orders SET status='expired' WHERE order_id=? "
                "AND status IN ('awaiting_payment','confirming') "
                "AND expires_at<=? AND license_key IS NULL",
                (order_id, now))
        return cur.rowcount == 1

    def mark_confirming(self, order_id, txid, confirmations):
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE orders SET status='confirming', txid=?, "
                "confirmations=? WHERE order_id=? AND status IN "
                "('awaiting_payment','confirming') AND license_key IS NULL",
                (txid, confirmations, order_id))

    def set_confirmations(self, order_id, confirmations):
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE orders SET confirmations=? WHERE order_id=?",
                (confirmations, order_id))

    def claim_and_fulfill(self, order_id, license_key, license_id, paid_at):
        """THE minting claim — atomic and idempotent.

        Exactly one caller, ever, transitions an open order to paid
        with its license. Everyone else (second poll, post-restart
        poll) gets False and the already-stored key is the only key.
        """
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE orders SET status='paid', license_key=?, "
                "license_id=?, paid_at=? WHERE order_id=? AND status IN "
                "('awaiting_payment','confirming') AND license_key IS NULL",
                (license_key, license_id, paid_at, order_id))
        return cur.rowcount == 1

    def set_delivery(self, order_id, delivery, note=""):
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE orders SET delivery=?, delivery_note=? "
                "WHERE order_id=?", (delivery, note, order_id))

    def find_orders_by_total(self, total_sats):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM orders WHERE total_sats=? "
                "ORDER BY created_at DESC", (total_sats,)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------- payment events

    def mark_payment_seen(self, txid, vout_index, amount_sats):
        """Returns True the first time a (txid, vout) is seen."""
        ref = "%s:%d" % (txid, vout_index)
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO seen_payments(payment_ref,txid,"
                "amount_sats,seen_at) VALUES (?,?,?,?)",
                (ref, txid, amount_sats, int(time.time())))
        return cur.rowcount == 1

    def log_event(self, kind, order_id=None, txid=None, amount_sats=None,
                  detail=""):
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO payment_events(ts,kind,order_id,txid,"
                "amount_sats,detail) VALUES (?,?,?,?,?,?)",
                (int(time.time()), kind, order_id, txid, amount_sats,
                 detail))

    def list_events(self, limit=100):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM payment_events ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
        return [dict(r) for r in rows]

    # --------------------------------------------------------- certificates

    def get_certificate(self, lic_id, cert_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM certificates WHERE lic_id=? AND cert_id=?",
                (lic_id, cert_id)).fetchone()
        return dict(row) if row else None

    def add_certificate(self, cert):
        """Insert an issued certificate. Returns the stored row —
        on a UNIQUE conflict returns the pre-existing row instead
        (idempotent issuance)."""
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO certificates(lic_id,cert_id,"
                "email,name,score,pct,cert_date,payload_json,"
                "countersigned_code,cert_html,delivered,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (cert["lic_id"], cert["cert_id"], cert["email"],
                 cert["name"], cert["score"], cert["pct"],
                 cert.get("cert_date"), cert["payload_json"],
                 cert["countersigned_code"], cert["cert_html"],
                 1 if cert.get("delivered") else 0,
                 int(time.time())))
        return self.get_certificate(cert["lic_id"], cert["cert_id"])

    def set_certificate_delivered(self, lic_id, cert_id):
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE certificates SET delivered=1 WHERE lic_id=? "
                "AND cert_id=?", (lic_id, cert_id))

    # --------------------------------------------------------- review queue

    def enqueue_review(self, item):
        """Hold a flagged certificate for the owner. Idempotent on
        (lic_id, cert_id): resubmission returns the existing entry."""
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO review_queue(lic_id,cert_id,"
                "email,name,score,pct,payload_json,license_key,"
                "integrity_json,status,received_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,'held',?)",
                (item.get("lic_id"), item.get("cert_id"), item["email"],
                 item.get("name"), item.get("score"), item.get("pct"),
                 item["payload_json"], item["license_key"],
                 item.get("integrity_json"), int(time.time())))
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM review_queue WHERE lic_id IS ? AND "
                "cert_id IS ?", (item.get("lic_id"),
                                 item.get("cert_id"))).fetchone()
        return dict(row) if row else None

    def list_review(self, include_resolved=False):
        q = "SELECT * FROM review_queue"
        if not include_resolved:
            q += " WHERE status='held'"
        q += " ORDER BY id DESC"
        with self._lock:
            rows = self._conn.execute(q).fetchall()
        return [dict(r) for r in rows]

    def get_review(self, review_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM review_queue WHERE id=?",
                (review_id,)).fetchone()
        return dict(row) if row else None

    def set_review_status(self, review_id, status):
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE review_queue SET status=? WHERE id=?",
                (status, review_id))
        return cur.rowcount == 1
