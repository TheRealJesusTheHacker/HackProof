# HackProof Payments — automated Bitcoin checkout + certificate issuance

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](../README.md)
[![License: PROPRIETARY](https://img.shields.io/badge/license-PROPRIETARY-red?style=flat-square)](../LICENSE)

> **Deployment status — built and ready, not yet live.** This service is
> complete and tested, but it is **not yet deployed on the owner's server**
> and is therefore **not processing live orders**. The site constants that
> wire the pages to it — `PAYMENTS_API_BASE` in `game/buy.html` and in
> `exam.html` — are currently `""`, so the live buy page runs its interim
> mode (live CoinGecko $5 amount plus the manual fulfilment paths) and
> certificate countersigning runs through the manual `sign-cert` tool.
> Deploying this service and setting those constants is the remaining
> owner step; everything below describes the service as built.

This service replaces manual, email-me-your-transaction-ID fulfilment
with automation, in the owner's settled model:

> **They send the Bitcoin. We detect it, a key is automatically
> generated and sent to them, and that key is their access to
> premium.**

**There is no account system and there never will be.** No usernames,
no passwords, no login. The minted license key **is** the buyer's
account and their only credential; email delivery is the primary path,
and the order-status endpoint is the backup claim path for a lost
email. Course completion works the same way: a passed exam with a
clean integrity verdict gets its certificate countersigned, generated,
and emailed automatically.

The service is a small Python program (standard library + the
`cryptography` package — the same single dependency
`tools/keygen.py` already has). It runs on the seller's own machine
(Windows next to Sentinel Live, or Linux), reads the seller's existing
`~/.hackproof` key store, watches the public purchase address on a
public block explorer API, and sends mail through the seller's own
SMTP mailbox. It holds **no Bitcoin keys** and cannot move funds.

---

## How a purchase flows

```
buyer                buy page                 this service            chain
  |  enters email        |                          |                     |
  |--------------------->|  POST /api/orders        |                     |
  |                      |------------------------->| locks $5 price,     |
  |                      |                          | converts via        |
  |                      |                          | CoinGecko, assigns  |
  |                      |   {order_id, address,    | a UNIQUE exact BTC  |
  |  pays exact amount   |    exact BTC amount}     | amount              |
  |-------------------------------------------------|-------------------->|
  |                      |  GET /api/orders/<id>     |  polls mempool.space|
  |                      |<------- confirming -----|  every ~30 s        |
  |                      |                          |  1 confirmation ->  |
  |                      |                          |  mints ONE license  |
  |  license key email   |<------- paid ------------|  (atomic, once)     |
  |<---------------------  (key = the account)       |                     |
```

1. **Order.** `POST /api/orders` locks the USD price ($5, in config)
   and the live BTC/USD rate (CoinGecko — the same source the buy
   page uses) into the order, then assigns a **unique exact amount**:
   the base satoshis for $5 plus a small per-order satoshi offset
   (1–999). Because every order pays the *same* address, that exact
   amount is how a payment is matched to its order. The payment
   window is **2 hours** (configurable).
2. **Watch.** A poller checks the esplora-compatible API
   (mempool.space by default) for payments to the purchase address.
   A payment whose satoshi amount exactly matches an open order moves
   it to `confirming`. At **1 confirmation** (configurable) the order
   is fulfilled.
3. **Mint — exactly once.** Minting uses the *same* license scheme
   (and byte-compatible code) as `tools/keygen.py`: an Ed25519-signed
   premium license wrapping the content key from the host's
   `~/.hackproof` store. The fulfilment claim is a single conditional
   database update — an order can never mint twice: not on a second
   poll, not after a restart, not if two watchers race. A
   service-minted key is indistinguishable from a keygen-minted one
   (the test suite proves keygen itself accepts them, both ways).
4. **Deliver.** The key is emailed (see the copy rules below). If SMTP
   is not configured, the delivery is *claim-only*: the buyer
   retrieves the key from the order-status endpoint, and the service
   logs the skipped email loudly. It never pretends mail was sent.

## How a certificate flows

```
student passes exam -> POST /api/certificates
   -> payload validated EXACTLY like `tools/keygen.py sign-cert`
      (score 72-90 of 90, pct exactly consistent with the score,
       license binding, Ed25519-valid license, HMAC proof verified)
   -> integrity verdict CLEAN  -> countersigned server-side,
      finished certificate generated (same design the exam page
      renders), emailed with the certificate attached + the
      verification code + the public verify page. Idempotent:
      one certificate per license + exam pass; resubmissions
      return the existing issuance.
   -> integrity verdict FLAGGED (or missing/unreadable)
      -> NOT auto-sent — see the hold policy below.
```

---

## API contract (what the site wires to)

Base URL is configurable on the site side (e.g.
`PAYMENTS_API_BASE`). All bodies are JSON. CORS is open — the
storefront is served from a different origin than this service.

### `POST /api/orders`
Request: `{ "email": "buyer@example.com" }` — the email is where the
key will be delivered, so it is validated.

`201` response:
```json
{
  "order_id": "long-random-token",
  "status": "awaiting_payment",
  "btc_address": "bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0",
  "btc_amount_sats": 123457,
  "btc_amount_btc": "0.00123457",
  "price_usd": 5.0,
  "confirmations": 0,
  "expires_at": "2026-10-19T21:00:00Z"
}
```
Errors: `400` invalid email · `503` price source unavailable ·
`429` rate limited.

### `GET /api/orders/<order_id>`
`200` response: the same fields, with `status` one of
`awaiting_payment | confirming | paid | expired` and
`confirmations` current. **When `paid`, the response also includes
`license_key`.** This is deliberate: the `order_id` is a long random
token and *is* the claim credential — whoever holds the order link
can retrieve the key. That is the lost-email backup path, and it is
why the order link must be treated like a receipt with a key printed
on it. `404` for unknown ids.

### `POST /api/certificates`
Request:
```json
{
  "certificate_code": "<base64 unsigned payload code from exam.html>",
  "license_key": "<the student's premium license key>",
  "email": "student@example.com",
  "integrity": { "verdict": "clean", "...": "the exam integrity block" }
}
```
- `certificate_code` is the base64 code exactly as the exam page
  produces it. (A `payload` JSON object may be sent instead of
  `certificate_code`; the code form is preferred because it is
  byte-exact.)
- `license_key` is **required**: the payload's HMAC proof is keyed by
  the license secret, so — exactly like the manual sign-cert flow —
  the proof cannot be verified without the key that earned it.
- `integrity` is the exam integrity layer's verdict block. `clean`
  auto-issues; **anything else — flagged, missing, or unreadable —
  fails closed to the review hold.**

Responses:
- `201 { "status": "issued", "cert_id", "countersigned_code",
  "verify_url", "delivered" }` — certificate countersigned, generated,
  and emailed (attachment + code in the body).
- `200` same shape — this license+exam pass was already issued;
  returns the existing issuance (and re-sends the email if the first
  send failed). Never a duplicate.
- `202 { "status": "held_for_review", "cert_id", "detail" }` —
  integrity hold (below).
- `400 { "error": "..." }` — validation failed: failing or impossible
  score (e.g. 71/79, 100/90), percentage inconsistent with the score,
  license/payload binding mismatch, bad or missing HMAC proof,
  already-signed payload, malformed code. **All rejections are final
  and identical to what `tools/keygen.py sign-cert` refuses.**

### Owner-only admin (review queue + problem payments)
Enabled only when `admin_token` is set in the host config; the token
goes in the `X-Admin-Token` header.
- `GET /api/admin/review` — held certificates (metadata) + recent
  payment events needing manual resolution.
- `GET /api/admin/review/<id>` — the full held record, including the
  payload and the student's license key, ready to paste into the
  manual tool.
- `POST /api/admin/review/<id>/resolve` `{ "status": "resolved" |
  "dismissed" }`.
- On the host itself, `python3 service.py --list-review` prints the
  same digest without the API.

### `GET /healthz` → `{ "ok": true }`

---

## The flagged-certificate hold (a deliberate design choice)

Exam integrity signals are evidence, not proof — and automation must
never rubber-stamp an exam the integrity layer questioned. So a
flagged (or unverifiable) integrity verdict **stops the line**: the
payload — which itself passed every cryptographic check — is held in
a host-side review queue, logged at WARNING, and surfaced to the
owner through the admin endpoints / `--list-review`. The owner then
decides and, if satisfied, countersigns manually with the existing
tool:

```
python3 tools/keygen.py sign-cert --license <student's key> <code>
```

Clean exams are never delayed by this. Flagged exams are never
auto-sent. That split is intentional and is not a bug to "fix."

## Problem payments (manual fallback preserved)

Payments that don't cleanly fulfil an open order **never auto-mint**.
They are written to the payment-event log (visible in
`--list-review` and the admin endpoint) for the owner's manual
resolution — the old manual flow is the standing fallback:

| kind        | meaning                                                    |
|-------------|------------------------------------------------------------|
| `unmatched` | amount matches no order — wrong amount or unsolicited      |
| `late`      | amount matched an order whose 2-hour window had closed     |
| `duplicate` | a second payment for an already-paid (or already-bound) order |
| `wrong-amount` sends, underpayments, and exchange/batched payouts land here too — an exchange that pays many customers in one transaction cannot produce the order's unique exact amount per customer, so those buyers are resolved by hand. |

Underpayments are not partially credited and overpayments are not
auto-refunded: the owner reissues or refunds manually, as before.

## Honest limits

- **Single address + unique-amount matching.** Matching is by exact
  satoshi amount on one published address. It is simple and robust
  for this price point, but it is not HD-wallet-per-order
  addressing; the offset space (999 concurrent open orders) is the
  ceiling, and amounts recycle as orders close.
- **Buyers must send the exact amount.** Wallets that round, deduct
  fees from the amount, or batch payments (most exchanges) will miss
  the exact figure and fall to manual resolution. The buy page must
  say "send exactly this amount, from a wallet you control."
- **Confirmation policy** is 1 confirmation by default — appropriate
  for a $5 digital good; raise it in config if the threat model
  changes.
- **Public explorer dependency.** Watching uses mempool.space's
  public esplora API; point `esplora_base` at any compatible
  instance (including a self-hosted one) if that ever matters.
- **Email is best-effort by design.** SMTP failures never lose a
  key: the claim endpoint is the permanent backup, and undelivered
  certificates re-send on resubmission.

## Security model

- **Key custody.** The Ed25519 private key and content key are read
  from the host's existing `~/.hackproof` store (the one
  `tools/keygen.py setup` creates, files mode 600). They are never
  copied into this repo, the order database, the logs, or any email.
  If the store is missing or inconsistent (e.g. the stored public
  key doesn't match the private key), **the service refuses to
  start**, with a message saying exactly what to run.
- **What's sensitive in the data dir.** `~/.hackproof-payments/
  hackproof-payments.db` (created mode 600) holds orders, issued
  license keys (bearer credentials — the key *is* the account), and
  held-certificate records including the student-submitted license
  keys (kept so the owner can run the manual sign-cert tool).
  Protect it like the product it unlocks: host account access only.
- **Attack surface.** The API creates orders and accepts certificate
  submissions; every issuance decision is gated by the same
  cryptographic checks as the manual tool, so a forged payload is
  worth exactly as much here as it was against keygen: nothing.
  Basic per-IP rate limiting is built in (10 order-creates/min,
  10 cert-submits/min, 60 status reads/min). The admin endpoints are
  token-gated and disabled entirely when no token is configured.
- **Secrets in config.** The SMTP password and admin token live only
  in the host's config file (mode 600). `config.example.json` ships
  placeholders; never commit a filled-in copy.
- **No funds risk.** The service watches a public address; it has no
  wallet, no private keys for Bitcoin, and cannot broadcast.

## Host setup

Prereqs on the host: Python 3.10+, then
`pip install -r payments/requirements.txt` (just `cryptography`),
and the seller key store must already exist (`python3 tools/keygen.py
setup` — if the site is live-selling, it does).

1. Copy `payments/config.example.json` to
   `~/.hackproof-payments/config.json`, fill in SMTP + a long random
   `admin_token`, and lock it down:
   - Linux/macOS: `chmod 600 ~/.hackproof-payments/config.json`
   - Windows: keep it in your user profile; don't share the folder.
2. Sanity-check: `python3 payments/service.py --check`
   (validates config + key store, then exits).
3. Dress rehearsal, no network, no money:
   `python3 payments/service.py --selftest`
4. Run it: `python3 payments/service.py`
   (default bind `127.0.0.1:8787`; put your existing reverse proxy /
   tunnel in front of it for the public site, or set `bind` in
   config if the network setup calls for it).

### Run at boot, next to Sentinel Live

**Windows (Task Scheduler)** — same pattern as the other Sentinel
services:
- Action: `pythonw.exe` (or `python.exe`) with arguments
  `"C:\path\to\HackProof\payments\service.py"`, Start in:
  `C:\path\to\HackProof\payments`.
- Trigger: At startup (or At log on), with "Restart on failure".

**Linux (systemd)** — `/etc/systemd/system/hackproof-payments.service`:
```ini
[Unit]
Description=HackProof payment + certificate service
After=network-online.target

[Service]
WorkingDirectory=/opt/HackProof/payments
ExecStart=/usr/bin/python3 /opt/HackProof/payments/service.py
Restart=on-failure
User=<the account that owns ~/.hackproof>

[Install]
WantedBy=multi-user.target
```
Then `systemctl enable --now hackproof-payments`.

### Operations

- `--once` — a single watcher poll, then exit (cron-friendly).
- `--list-review` — the owner digest: held certificates + payment
  events needing manual resolution.
- Logs are structured single-line records on stdout/stderr:
  orders, confirmations, mints, deliveries, holds, and every problem
  payment, each with its order id / txid for cross-checking against a
  block explorer.

## Configuration reference

Everything lives in one JSON file (see `config.example.json`).
Defaults shown; secrets marked 🔒 live only in the host copy.

| key | default | meaning |
|---|---|---|
| `bind` / `port` | `127.0.0.1` / `8787` | HTTP listen address |
| `btc_address` | the buy page's address | purchase address to watch |
| `price_usd` | `5.00` | premium price (locked per order) |
| `license_days` | `365` | license lifetime minted per order |
| `required_confirmations` | `1` | confirmations before minting |
| `order_ttl_seconds` | `7200` | payment window (2 h) |
| `max_order_offset_sats` | `999` | unique-amount space |
| `keydir` | `~/.hackproof` | seller key store location |
| `data_dir` | `~/.hackproof-payments` | SQLite store + (default) config home |
| `esplora_base` | `https://mempool.space/api` | chain API |
| `coingecko_url` | CoinGecko simple/price | BTC/USD source (same as the site) |
| `poll_interval_seconds` | `30` | watcher cadence |
| `admin_token` 🔒 | `""` (admin off) | gates `/api/admin/*` |
| `smtp.host/port/security/username/password` 🔒 | — | mailbox SMTP; empty host = claim-only delivery |
| `smtp.from_address/from_name` | business mailbox / `Sentinel Safeguard` | sender identity |
| `verify_url` / `site_url` / `support_email` | live site values | used in outgoing mail |

## The two emails

**License delivery** — subject "Your HackProof Premium license key."
It carries the key, and says plainly, in the owner's words made copy:
**this key is your account** — HackProof has no usernames or
passwords; save the key like something irreplaceable, because whoever
holds it holds the premium access; plus redeem steps, the 365-day
term, and the claim fallback for a lost email.

**Certificate delivery** — from Sentinel Safeguard, subject naming
the achievement ("Your Sentinel Safeguard Certificate of Cyber
Security Awareness Course Completion"). Body: score, certificate ID,
date, verification instructions and the public verify page, and the
countersigned verification code; the finished certificate itself is
attached as a print-ready HTML file matching the exam page's design
(cream stock, double border, verified seal lit).

## Tests

```
python3 -m unittest discover -s payments/tests -v
python3 payments/service.py --selftest
```

The suite (29 tests) stubs CoinGecko, the esplora API, and SMTP — no
live network. It proves, against the **real** `tools/keygen.py`:

- service-minted keys are accepted by keygen and unwrap the real
  content key; keygen-minted keys verify in the service;
- certificate accept/refuse equivalence across the forged-case
  matrix (failing 71/79, impossible 100/90, mismatched percentage,
  wrong license, tampered payload, missing proof, already-signed),
  and byte-identical countersigned output on genuine passes
  (including the 72 and 90 boundaries);
- watcher behaviour: exact-amount matching, 0-conf stays confirming,
  1-conf mints exactly once, restart idempotency, expired orders
  never mint, wrong amounts and duplicate payments never mint and
  are logged for the owner;
- certificates: clean issues + emails once, flagged is held and
  never sent, duplicate submissions return the existing issuance.

## Note on PRIVACY.md

`PRIVACY.md` (repo root, legal content — not edited from here) already
describes the automated purchase and certificate flows this service
implements: the buyer's email and order link are the fulfilment record,
and the order ID is documented there as a claim credential to keep
private. This service changes nothing else about the site's privacy
posture: still no accounts, no tracking, no third-party analytics.
