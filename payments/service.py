#!/usr/bin/env python3
"""HackProof automated payment + certificate service — entry point.

  python3 service.py [--config config.json]          run the service
  python3 service.py --selftest                     stubbed dress
                                                      rehearsal, no
                                                      network, no money
  python3 service.py --once                         one watcher poll,
                                                      then exit
  python3 service.py --list-review                  print the owner
                                                      digest: held
                                                      certificates +
                                                      payments needing
                                                      manual resolution
  python3 service.py --check                        validate config +
                                                      key store, then
                                                      exit

The service REFUSES to start without the host key store
(~/.hackproof, from `tools/keygen.py setup`) — a payment service
that cannot mint must be loudly down, never silently open.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hackproof_pay import crypto_core  # noqa: E402
from hackproof_pay.chain import EsploraClient  # noqa: E402
from hackproof_pay.config import Config, ConfigError  # noqa: E402
from hackproof_pay.httpd import App, make_server  # noqa: E402
from hackproof_pay.mailer import Mailer  # noqa: E402
from hackproof_pay.pricing import Pricer  # noqa: E402
from hackproof_pay.store import Store  # noqa: E402


def build_app(cfg):
    keys = crypto_core.load_keystore(cfg["keydir"])
    store = Store(cfg.db_path)
    pricer = Pricer(cfg["coingecko_url"], cfg["price_usd"],
                    cache_seconds=int(cfg["rate_cache_seconds"]))
    chain = EsploraClient(cfg["esplora_base"])
    mailer = Mailer(cfg["smtp"], cfg["support_email"])
    app = App(cfg, store, keys, mailer, pricer, chain)
    return app


def cmd_list_review(cfg):
    store = Store(cfg.db_path)
    held = store.list_review()
    events = store.list_events(50)
    print("== Certificates held for owner review: %d ==" % len(held))
    for item in held:
        print("  #%d cert=%s lic=%s name=%r score=%s/%s email=%s" % (
            item["id"], item["cert_id"], item["lic_id"], item["name"],
            item["score"], item["pct"], item["email"]))
        print("      integrity: %s" % item["integrity_json"])
        print("      countersign manually: fetch the full record via "
              "GET /api/admin/review/%d, then run" % item["id"])
        print("      tools/keygen.py sign-cert --license <key> <code>")
    print("== Payment events needing manual resolution: %d =="
          % len(events))
    for ev in events:
        print("  [%s] kind=%s order=%s txid=%s amount=%s — %s" % (
            ev["ts"], ev["kind"], ev["order_id"], ev["txid"],
            ev["amount_sats"], ev["detail"]))
    store.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="HackProof payment + certificate service")
    ap.add_argument("--config", default=None,
                    help="path to config JSON (default: "
                         "~/.hackproof-payments/config.json if present)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--list-review", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if args.selftest:
        from hackproof_pay.selftest import run_selftest
        return run_selftest()

    cfg_path = args.config
    if cfg_path is None:
        candidate = os.path.expanduser(
            "~/.hackproof-payments/config.json")
        if os.path.exists(candidate):
            cfg_path = candidate
    try:
        cfg = Config.load(cfg_path)
    except (ConfigError, json.JSONDecodeError) as exc:
        print("CONFIG ERROR: %s" % exc, file=sys.stderr)
        return 2
    if cfg_path is None:
        logging.warning("no config file found — running on built-in "
                        "defaults; SMTP and admin endpoints are OFF "
                        "until configured")
    try:
        keys = crypto_core.load_keystore(cfg["keydir"])
    except crypto_core.KeyStoreError as exc:
        print("KEY STORE ERROR: %s" % exc, file=sys.stderr)
        return 2
    logging.info("key store OK (public key %s…)",
                 keys.public_key_hex[:16])

    if args.check:
        print("config + key store OK")
        return 0
    if args.list_review:
        return cmd_list_review(cfg)

    app = build_app(cfg)
    if args.once:
        app.watcher.poll_once()
        print("one poll complete")
        return 0

    stop = threading.Event()

    def watch_loop():
        while not stop.is_set():
            try:
                app.watcher.poll_once()
            except Exception as exc:  # the loop must outlive a bad poll
                logging.error("watcher poll crashed: %s", exc)
            stop.wait(int(cfg["poll_interval_seconds"]))

    thread = threading.Thread(target=watch_loop, daemon=True,
                              name="watcher")
    thread.start()
    server = make_server(app, cfg["bind"], int(cfg["port"]))
    logging.info("HackProof payments listening on %s:%s — watching %s",
                 cfg["bind"], cfg["port"], cfg["btc_address"])
    if not app.mailer.configured:
        logging.warning("SMTP not configured: keys and certificates "
                        "will be delivered by CLAIM ONLY (order "
                        "status endpoint) until SMTP is set up")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("shutting down")
    finally:
        stop.set()
        server.shutdown()
        app.store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
