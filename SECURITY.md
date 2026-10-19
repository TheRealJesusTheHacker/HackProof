# HackProof — Security Policy

## Reporting a vulnerability

Found a security issue in HackProof? Email us directly:

**Sentinelsafeguard@outlook.com**

Please include:
- A description of the issue and its potential impact
- Steps to reproduce (or a proof of concept)
- Your contact info so we can follow up

We ask that you give us a reasonable chance to fix confirmed issues before
disclosing them publicly. We will acknowledge receipt and keep you posted
on the fix.

## License-key cryptography (high-level design)

HackProof premium content is protected by an offline license-key system:

- **Ed25519** digital signatures — each license key is signed by the
  publisher. The course app ships with only the public key, so keys are
  verified locally and cannot be forged without the private signing key.
- **AES-256-GCM** authenticated encryption — the premium content pack is
  encrypted at rest; a valid license key unlocks the decryption material
  on the student's own device.

No key material is published in this repository. If you believe the
license system is bypassable, report it to the email above rather than
publishing an exploit — see [TERMS.md](TERMS.md).

## Scope

In scope: the course client (`game/`), the buy page (`game/buy.html`), and
the license tooling design (`tools/keygen.py`).

Out of scope: third-party services linked from the site (e.g. the BTC
price feed on the buy page), and social-engineering of the maintainer.
