"""Service configuration: a JSON file on the host (never in the repo
with real values — see config.example.json).

Secrets (SMTP password, admin token) live ONLY in the host's config
file. The repository carries an example with placeholders.
"""

from __future__ import annotations

import json
import os

DEFAULTS = {
    "bind": "127.0.0.1",
    "port": 8787,
    # The HackProof purchase address (same one buy.html shows).
    "btc_address": "bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0",
    "price_usd": 5.00,
    "license_days": 365,
    "required_confirmations": 1,
    "order_ttl_seconds": 7200,          # 2-hour payment window
    "max_order_offset_sats": 999,       # unique-amount matching space
    "keydir": "~/.hackproof",           # the keygen.py key store
    "data_dir": "~/.hackproof-payments",
    "esplora_base": "https://mempool.space/api",
    # Same price source the buy page uses.
    "coingecko_url": "https://api.coingecko.com/api/v3/simple/price"
                     "?ids=bitcoin&vs_currencies=usd",
    "rate_cache_seconds": 60,
    "poll_interval_seconds": 30,
    "verify_url": "https://therealjesusthehacker.github.io/HackProof/"
                  "verify.html",
    "site_url": "https://therealjesusthehacker.github.io/HackProof/",
    "support_email": "Sentinelsafeguard@outlook.com",
    # Empty admin_token disables the owner-only admin endpoints.
    "admin_token": "",
    "smtp": {
        "host": "",
        "port": 587,
        "security": "starttls",         # starttls | ssl | none
        "username": "",
        "password": "",
        "from_address": "Sentinelsafeguard@outlook.com",
        "from_name": "Sentinel Safeguard",
    },
}


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, values):
        self._v = values

    def __getitem__(self, key):
        return self._v[key]

    def get(self, key, default=None):
        return self._v.get(key, default)

    @property
    def data_dir(self):
        return os.path.expanduser(self._v["data_dir"])

    @property
    def db_path(self):
        return os.path.join(self.data_dir, "hackproof-payments.db")

    @property
    def smtp_configured(self):
        return bool(self._v["smtp"].get("host"))

    @classmethod
    def load(cls, path=None):
        values = json.loads(json.dumps(DEFAULTS))  # deep copy
        if path:
            if not os.path.exists(path):
                raise ConfigError("config file not found: %s" % path)
            with open(path, encoding="utf-8") as f:
                user = json.load(f)
            for k, v in user.items():
                if k == "smtp" and isinstance(v, dict):
                    values["smtp"].update(v)
                else:
                    values[k] = v
        if not values["btc_address"]:
            raise ConfigError("btc_address must be set")
        if not (isinstance(values["price_usd"], (int, float))
                and values["price_usd"] > 0):
            raise ConfigError("price_usd must be a positive number")
        if int(values["required_confirmations"]) < 0:
            raise ConfigError("required_confirmations must be >= 0")
        if int(values["order_ttl_seconds"]) <= 0:
            raise ConfigError("order_ttl_seconds must be positive")
        return cls(values)
