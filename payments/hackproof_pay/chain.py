"""Blockchain watching via a public esplora-compatible API
(default: mempool.space). Read-only — the service never holds BTC
keys and never broadcasts anything; it only watches the purchase
address the buy page already publishes.
"""

from __future__ import annotations

import json

from .pricing import default_fetcher


class ChainError(Exception):
    pass


class EsploraClient:
    def __init__(self, base_url, fetcher=None):
        self._base = base_url.rstrip("/")
        self._fetch = fetcher or default_fetcher

    def tip_height(self) -> int:
        status, body = self._fetch(self._base + "/blocks/tip/height")
        if status != 200:
            raise ChainError("tip height: HTTP %s" % status)
        try:
            return int(body.strip())
        except ValueError:
            raise ChainError("tip height: unusable body")

    def address_txs(self, address):
        """Recent transactions for the address (confirmed + mempool),
        esplora shape: [{txid, vout:[{scriptpubkey_address, value}],
        status:{confirmed, block_height}}]."""
        status, body = self._fetch(
            self._base + "/address/%s/txs" % address)
        if status != 200:
            raise ChainError("address txs: HTTP %s" % status)
        try:
            txs = json.loads(body)
        except Exception:
            raise ChainError("address txs: unusable body")
        if not isinstance(txs, list):
            raise ChainError("address txs: unexpected shape")
        return txs


def payments_to_address(tx, address):
    """Yield (vout_index, value_sats) for outputs paying `address`."""
    for i, vout in enumerate(tx.get("vout") or []):
        if vout.get("scriptpubkey_address") == address:
            value = vout.get("value")
            if isinstance(value, int) and value > 0:
                yield i, value


def confirmations(tx, tip_height):
    """0 while unconfirmed; else tip - block_height + 1."""
    status = tx.get("status") or {}
    if not status.get("confirmed"):
        return 0
    height = status.get("block_height")
    if not isinstance(height, int) or tip_height is None:
        return 1  # confirmed but height unknown: at least 1
    return max(1, tip_height - height + 1)
