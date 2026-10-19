"""Pricing: USD -> integer satoshis, and unique-amount allocation.

All money math after the rate fetch is INTEGER satoshis. The rate comes
from CoinGecko — the same source buy.html uses — and is locked into the
order at creation; later rate moves never change an open order.

Order matching key: because every order pays the SAME address, each
open order gets a unique total = base_sats + a small per-order satoshi
offset. A payment is matched to an order by its exact satoshi amount.
"""

from __future__ import annotations

import json
import time
import urllib.request

SATS_PER_BTC = 100_000_000


def default_fetcher(url, timeout=15):
    """fetcher(url) -> (status, body_text). Injectable for tests."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "HackProof-Payments/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


class PricingError(Exception):
    pass


class Pricer:
    def __init__(self, coingecko_url, price_usd, fetcher=None,
                 cache_seconds=60):
        self._url = coingecko_url
        self._price_usd = float(price_usd)
        self._fetch = fetcher or default_fetcher
        self._cache_seconds = cache_seconds
        self._cached = None  # (rate_usd, fetched_at)

    def btc_rate_usd(self):
        now = time.time()
        if self._cached and now - self._cached[1] < self._cache_seconds:
            return self._cached[0]
        status, body = self._fetch(self._url)
        if status != 200:
            raise PricingError("price source returned HTTP %s" % status)
        try:
            rate = json.loads(body)["bitcoin"]["usd"]
            rate = float(rate)
        except Exception:
            raise PricingError("price source returned an unusable body")
        if not rate > 0:
            raise PricingError("price source returned a non-positive rate")
        self._cached = (rate, now)
        return rate

    def base_sats(self, rate_usd=None):
        """The $5-equivalent in satoshis at the given (or live) rate —
        same rounding the buy page's toFixed(8) produces."""
        rate = rate_usd if rate_usd is not None else self.btc_rate_usd()
        return int(round(self._price_usd / rate * SATS_PER_BTC))


def sats_to_btc_str(sats: int) -> str:
    """Exact 8-decimal BTC string for an integer satoshi amount."""
    return "%d.%08d" % (sats // SATS_PER_BTC, sats % SATS_PER_BTC)


def allocate_total(base_sats, reserved_totals, max_offset):
    """Pick (total_sats, offset) whose total is unique among open
    orders. Smallest free offset wins; offsets recycle as orders
    close. Raises PricingError when the offset space is exhausted."""
    for offset in range(1, max_offset + 1):
        total = base_sats + offset
        if total not in reserved_totals:
            return total, offset
    raise PricingError(
        "too many open orders — unique-amount space exhausted "
        "(%d offsets in use)" % max_offset)
