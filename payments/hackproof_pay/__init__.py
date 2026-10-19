"""HackProof automated payment + certificate service (server-side).

Detects Bitcoin payments to the HackProof address, mints premium license
keys with the exact scheme tools/keygen.py defines, emails them to buyers,
and auto-issues countersigned exam certificates for clean exam passes.

The license key IS the buyer's account — there is no login system.
"""

__version__ = "1.0.0"
