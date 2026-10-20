"""The watcher: polls the chain, matches payments to orders by exact
satoshi amount, mints exactly once per paid order, delivers the key.

State machine per order:
  awaiting_payment --(matching tx seen, confs < required)--> confirming
  confirming       --(confs >= required)--> paid (mint happens here,
                                             atomically, exactly once)
  awaiting/confirming --(window passes)--> expired

Payments that match nothing actionable NEVER mint. They are written to
the payment-event log for the owner's manual resolution — wrong
amount, late (order expired), duplicate (order already paid), or
unmatched — which keeps the old manual flow as the standing fallback.
"""

from __future__ import annotations

import logging
import re
import secrets
import threading
import time

from . import crypto_core
from .chain import confirmations, payments_to_address
from .mailer import license_email_body
from .pricing import allocate_total, sats_to_btc_str

log = logging.getLogger("hackproof_pay.watcher")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OrderError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class OrderService:
    def __init__(self, cfg, store, pricer):
        self._cfg = cfg
        self._store = store
        self._pricer = pricer
        # Serializes the reserve-allocate-insert sequence in
        # create_order: the reserved-totals read and the order
        # insert are separate store calls, so without this lock two
        # concurrent creations could read the same reserved set and
        # allocate the SAME total — and amount uniqueness is the
        # payment-matching key the whole watcher relies on.
        self._create_lock = threading.Lock()

    # ------------------------------------------------------------ orders

    def create_order(self, email):
        if not isinstance(email, str):
            raise OrderError("a valid email address is required — "
                             "your license key is delivered there")
        email = email.strip()
        if len(email) > 254 or not EMAIL_RE.match(email):
            raise OrderError("a valid email address is required — "
                             "your license key is delivered there")
        cfg = self._cfg
        rate = self._pricer.btc_rate_usd()       # may raise PricingError
        base = self._pricer.base_sats(rate)
        now = int(time.time())
        with self._create_lock:
            reserved = self._store.open_totals(now)
            total, offset = allocate_total(
                base, reserved, int(cfg["max_order_offset_sats"]))
            order = {
                "order_id": secrets.token_urlsafe(24),
                "email": email,
                "price_usd": float(cfg["price_usd"]),
                "rate_usd": rate,
                "base_sats": base,
                "offset_sats": offset,
                "total_sats": total,
                "btc_address": cfg["btc_address"],
                "created_at": now,
                "expires_at": now + int(cfg["order_ttl_seconds"]),
            }
            self._store.create_order(order)
        log.info("order created id=%s total_sats=%d offset=%d rate=%s",
                 order["order_id"], total, offset, rate)
        return self.public_order(self._store.get_order(
            order["order_id"]))

    def public_order(self, order):
        out = {
            "order_id": order["order_id"],
            "status": order["status"],
            "btc_address": order["btc_address"],
            "btc_amount_sats": order["total_sats"],
            "btc_amount_btc": sats_to_btc_str(order["total_sats"]),
            "price_usd": order["price_usd"],
            "confirmations": order.get("confirmations") or 0,
            "expires_at": _iso(order["expires_at"]),
        }
        if order["status"] == "paid" and order.get("license_key"):
            # The order id is the claim credential: whoever holds it
            # may retrieve the key (the backup for a lost email).
            out["license_key"] = order["license_key"]
            out["delivery"] = order.get("delivery")
        return out

    def get_order(self, order_id):
        order = self._store.get_order(order_id)
        if not order:
            return None
        if (order["status"] in ("awaiting_payment", "confirming")
                and order["expires_at"] <= int(time.time())):
            self._store.expire_order(order_id, int(time.time()))
            order = self._store.get_order(order_id)
        return self.public_order(order)


class Watcher:
    def __init__(self, cfg, store, chain, keystore, mailer):
        self._cfg = cfg
        self._store = store
        self._chain = chain
        self._keys = keystore
        self._mailer = mailer
        self._address = cfg["btc_address"]
        self._required = int(cfg["required_confirmations"])

    # ------------------------------------------------------------ polling

    def poll_once(self):
        cfg = self._cfg
        now = int(time.time())
        # 1) expire stale open orders first — a payment arriving for
        #    an expired order is "late", never a mint.
        for order in self._store.open_orders():
            if order["expires_at"] <= now:
                if self._store.expire_order(order["order_id"], now):
                    log.info("order expired id=%s", order["order_id"])
        # 2) fetch chain state (failures are logged, never fatal)
        try:
            tip = self._chain.tip_height()
            txs = self._chain.address_txs(self._address)
        except Exception as exc:
            log.error("chain poll failed: %s", exc)
            return
        # 3) match every payment output to the address
        for tx in txs:
            confs = confirmations(tx, tip)
            for vout_index, value in payments_to_address(tx, self._address):
                self._handle_payment(tx["txid"], vout_index, value,
                                     confs)

    def _handle_payment(self, txid, vout_index, value, confs):
        store = self._store
        first_sight = store.mark_payment_seen(txid, vout_index, value)
        # candidates sharing this exact total, newest first
        candidates = store.find_orders_by_total(value)
        open_match = next(
            (o for o in candidates
             if o["status"] in ("awaiting_payment", "confirming")), None)
        if open_match is not None:
            self._handle_open_match(open_match, txid, confs)
            return
        if not first_sight:
            return  # already classified on an earlier poll
        paid_match = next((o for o in candidates
                           if o["status"] == "paid"), None)
        expired_match = next((o for o in candidates
                              if o["status"] == "expired"), None)
        if paid_match is not None:
            kind, oid = "duplicate", paid_match["order_id"]
            detail = ("second payment of an already-paid order's "
                      "amount — owner resolves manually (reissue or "
                      "refund); nothing auto-minted")
        elif expired_match is not None:
            kind, oid = "late", expired_match["order_id"]
            detail = ("payment matched an expired order's amount — "
                      "owner resolves manually; nothing auto-minted")
        else:
            kind, oid = "unmatched", None
            detail = ("no open order with this exact amount — wrong "
                      "amount or unsolicited payment; owner resolves "
                      "manually; nothing auto-minted")
        store.log_event(kind, order_id=oid, txid=txid,
                        amount_sats=value, detail=detail)
        log.warning("payment event kind=%s txid=%s amount_sats=%d "
                    "order=%s", kind, txid, value, oid)

    def _handle_open_match(self, order, txid, confs):
        store = self._store
        oid = order["order_id"]
        if order.get("txid") and order["txid"] != txid:
            # A second, different tx paying an open order's amount:
            # the first tx keeps the order; log the extra loudly.
            if store.mark_payment_seen(txid, -1, order["total_sats"]):
                store.log_event(
                    "duplicate", order_id=oid, txid=txid,
                    amount_sats=order["total_sats"],
                    detail="second tx paying an open order already "
                           "bound to txid %s" % order["txid"])
                log.warning("duplicate payment tx for open order "
                            "id=%s txid=%s", oid, txid)
            return
        if confs >= self._required:
            self._fulfill(order, txid)
        else:
            store.mark_confirming(oid, txid, confs)
            log.info("order confirming id=%s txid=%s confs=%d/%d",
                     oid, txid, confs, self._required)

    # ---------------------------------------------------------- fulfillment

    def _fulfill(self, order, txid):
        store = self._store
        oid = order["order_id"]
        license_key, lic = crypto_core.mint_license(
            self._keys, days=int(self._cfg["license_days"]))
        claimed = store.claim_and_fulfill(
            oid, license_key, lic["id"], int(time.time()))
        if not claimed:
            # Someone (an earlier poll before a restart, a second
            # watcher) already fulfilled this order. The key we just
            # minted was never stored and is discarded — the stored
            # key is the one and only key for this order.
            log.info("order already fulfilled id=%s — duplicate mint "
                     "suppressed", oid)
            return
        log.info("order PAID id=%s lic_id=%s txid=%s", oid, lic["id"],
                 txid)
        self._deliver(order, license_key)

    def _deliver(self, order, license_key):
        cfg = self._cfg
        claim_hint = (
            "You can also retrieve your key anytime with your order "
            "link (the order status page shows it once your payment "
            "is confirmed), or email us your transaction ID and we "
            "will reissue it.")
        body = license_email_body(cfg, order, license_key, claim_hint)
        sent = self._mailer.send(
            order["email"], "Your HackProof Premium license key", body)
        if sent:
            self._store.set_delivery(order["order_id"], "sent",
                                     "license email sent")
        elif self._mailer.configured:
            self._store.set_delivery(order["order_id"], "failed",
                                     "SMTP send failed — claim via "
                                     "order status endpoint")
        else:
            self._store.set_delivery(order["order_id"], "claim_only",
                                     "SMTP not configured — claim via "
                                     "order status endpoint")


def _iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))
