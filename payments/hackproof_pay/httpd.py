"""HTTP API (stdlib http.server).

Routes:
  POST /api/orders                 create an order (locks price+amount)
  GET  /api/orders/<order_id>      order status; reveals the license
                                   key once paid (order id = claim
                                   credential)
  POST /api/certificates           exam completion -> auto-issue or
                                   owner-review hold
  GET  /api/admin/review           owner-only: held certificates +
                                   payment events needing resolution
  GET  /api/admin/review/<id>      owner-only: full held record (the
                                   payload + license for the manual
                                   sign-cert tool)
  POST /api/admin/review/<id>/resolve   owner-only: mark resolved /
                                   dismissed
  GET  /healthz                    liveness

Admin routes require the X-Admin-Token header to match the host
config's admin_token (constant-time compare); with no token
configured they are disabled outright. CORS is open for the API
routes — the storefront pages are served from a different origin
(GitHub Pages) than this service.
"""

from __future__ import annotations

import hmac
import json
import logging
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .certsvc import CertificateError, CertificateService
from .pricing import PricingError
from .watcher import OrderError, OrderService, Watcher
from . import crypto_core  # noqa: F401  (startup dependency check)

log = logging.getLogger("hackproof_pay.httpd")

MAX_BODY = 128 * 1024

# per-IP request budgets (per minute)
LIMITS = {"orders_write": 10, "orders_read": 60, "cert_write": 10,
          "admin": 30, "default": 120}


class RateLimiter:
    def __init__(self, limits=None, window=60):
        self._limits = limits or LIMITS
        self._window = window
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, bucket, ip):
        limit = self._limits.get(bucket, self._limits["default"])
        now = time.time()
        with self._lock:
            q = self._hits.setdefault((bucket, ip), deque())
            while q and now - q[0] > self._window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


class App:
    """Everything the handlers need, built once at startup."""

    def __init__(self, cfg, store, keystore, mailer, pricer, chain):
        self.cfg = cfg
        self.store = store
        self.keys = keystore
        self.mailer = mailer
        self.orders = OrderService(cfg, store, pricer)
        self.watcher = Watcher(cfg, store, chain, keystore, mailer)
        self.certs = CertificateService(cfg, store, keystore, mailer)
        self.limiter = RateLimiter()


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "HackProofPayments/1.0"

        # -- plumbing ------------------------------------------------
        def log_message(self, fmt, *args):
            log.debug("http %s %s", self.address_string(), fmt % args)

        def _send_json(self, status, obj):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                raise ValueError("request body too large")
            raw = self.rfile.read(length) if length else b""
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def _ip(self):
            return self.client_address[0]

        def _limited(self, bucket):
            if not app.limiter.allow(bucket, self._ip()):
                self._send_json(429, {"error": "too many requests — "
                                               "slow down and retry"})
                return True
            return False

        def _admin_ok(self):
            token = app.cfg.get("admin_token") or ""
            if not token:
                self._send_json(403, {"error": "admin endpoints are "
                                               "disabled (no "
                                               "admin_token configured)"})
                return False
            given = self.headers.get("X-Admin-Token") or ""
            if not hmac.compare_digest(given, token):
                self._send_json(401, {"error": "admin token required"})
                return False
            return True

        # -- routes ---------------------------------------------------
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods",
                             "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers",
                             "Content-Type, X-Admin-Token")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            try:
                if path == "/healthz":
                    return self._send_json(200, {"ok": True})
                if path.startswith("/api/orders/"):
                    if self._limited("orders_read"):
                        return
                    oid = path[len("/api/orders/"):]
                    order = app.orders.get_order(oid)
                    if not order:
                        return self._send_json(
                            404, {"error": "unknown order"})
                    return self._send_json(200, order)
                if path == "/api/admin/review":
                    if self._limited("admin") or not self._admin_ok():
                        return
                    held = app.store.list_review()
                    for item in held:
                        item.pop("license_key", None)
                        item.pop("payload_json", None)
                    return self._send_json(200, {
                        "held_certificates": held,
                        "payment_events": app.store.list_events(50),
                    })
                if path.startswith("/api/admin/review/"):
                    if self._limited("admin") or not self._admin_ok():
                        return
                    try:
                        rid = int(path.rsplit("/", 1)[1])
                    except ValueError:
                        return self._send_json(404,
                                               {"error": "unknown id"})
                    row = app.store.get_review(rid)
                    if not row:
                        return self._send_json(
                            404, {"error": "unknown review item"})
                    return self._send_json(200, row)
                return self._send_json(404, {"error": "not found"})
            except Exception as exc:  # never leak a bare 500 trace
                log.error("GET %s failed: %s", path, exc)
                return self._send_json(500, {"error": "internal error"})

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                body = self._read_json()
            except Exception:
                return self._send_json(400, {"error": "invalid JSON body"})
            try:
                if path == "/api/orders":
                    if self._limited("orders_write"):
                        return
                    try:
                        order = app.orders.create_order(
                            body.get("email"))
                    except OrderError as exc:
                        return self._send_json(exc.status,
                                               {"error": str(exc)})
                    except PricingError as exc:
                        return self._send_json(
                            503, {"error": "price source unavailable: "
                                           "%s" % exc})
                    return self._send_json(201, order)
                if path == "/api/certificates":
                    if self._limited("cert_write"):
                        return
                    try:
                        status, resp = app.certs.submit(body)
                    except CertificateError as exc:
                        return self._send_json(exc.status,
                                               {"error": str(exc)})
                    return self._send_json(status, resp)
                if path.startswith("/api/admin/review/") and \
                        path.endswith("/resolve"):
                    if self._limited("admin") or not self._admin_ok():
                        return
                    try:
                        rid = int(path.split("/")[-2])
                    except (ValueError, IndexError):
                        return self._send_json(404,
                                               {"error": "unknown id"})
                    new_status = (body.get("status") or "").strip()
                    if new_status not in ("resolved", "dismissed"):
                        return self._send_json(
                            400, {"error": "status must be 'resolved' "
                                           "or 'dismissed'"})
                    if not app.store.set_review_status(rid, new_status):
                        return self._send_json(
                            404, {"error": "unknown review item"})
                    return self._send_json(200, {"ok": True,
                                                 "id": rid,
                                                 "status": new_status})
                return self._send_json(404, {"error": "not found"})
            except Exception as exc:
                log.error("POST %s failed: %s", path, exc)
                return self._send_json(500, {"error": "internal error"})

    return Handler


def make_server(app, bind, port):
    server = ThreadingHTTPServer((bind, port), make_handler(app))
    server.daemon_threads = True
    return server
