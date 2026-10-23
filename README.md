# HackProof — Scam Defense & Cybersecurity Course

**46 modules, 7 tracks, plain language: from spotting a phish to the knowledge domains behind professional IT and security certifications — in an installable Windows app and in the browser.**

[![App release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/HackProof?filter=app-v*&style=flat-square&label=app%20release)](https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.5)
[![App build](https://img.shields.io/github/actions/workflow/status/TheRealJesusTheHacker/HackProof/build-app-windows.yml?style=flat-square&label=app%20build)](https://github.com/TheRealJesusTheHacker/HackProof/actions/workflows/build-app-windows.yml)
[![License: PROPRIETARY](https://img.shields.io/badge/license-PROPRIETARY-red?style=flat-square)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.5)
[![Site: GitHub Pages](https://img.shields.io/badge/site-GitHub%20Pages-green?style=flat-square)](https://therealjesusthehacker.github.io/HackProof/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](payments/README.md)

## Overview

**HackProof** is a commercial cybersecurity-education product built by **JesusTheHacker** (Sentinel Safeguard LLC). It teaches everyday people to recognize and defeat scams, and it carries serious students much further: the upper tracks teach the knowledge domains behind the certification ladder Sentinel Safeguard hires to.

Every module is written to one curriculum template: stated learning objectives, worked real-world case breakdowns, step-by-step procedures and checklists, a hands-on exercise, a knowledge check with answer feedback, key takeaways, a glossary, further reading from official sources, and a certification-alignment note that says exactly which certification domains the module supports — and what that does and does not mean (see *Certification alignment — honestly*, below).

HackProof comes in two forms that run the same course:

- **The Windows app (primary)** — one self-installing `HackProof.exe`, currently **app-v1.0.5**. The course, the final exam, certificate verification, and the premium screens run inside the app, and the unlocked course works fully offline. See [app/README.md](app/README.md).
- **The website** — a static GitHub Pages site in Sentinel green and black. It is the landing and download front door, the free web preview of the course, and home to the public certificate verify page.

The first **3 modules are free** — no account, no sign-up. The **premium tier is a one-time $5 USD in Bitcoin** and unlocks all 46 modules across 7 tracks, plus the 90-question final exam and a verifiable certificate of completion. There are no accounts anywhere in HackProof: a buyer's Ed25519-signed license key *is* the account, and it is validated offline on the student's own device.

## Status — what is live, what is built, what is pending

This section is kept honest on purpose. The three states below are different states, and the documentation does not blur them.

- **Live — the website.** The course site runs today on GitHub Pages: the free preview, the course catalog and reader, the buy page, the exam page, and the certificate verify page.
- **Released — the Windows app.** App release **app-v1.0.5** is published on GitHub Releases with two assets: `HackProof.exe` and `SHA256SUMS.txt`. The release build runs in the `build-app-windows.yml` workflow, which checks the tag against the app version in code, runs the app test suite, builds the exe with PyInstaller, and smoke-tests the built exe before attaching it to the release.
- **Built and ready — the payments service.** The automated Bitcoin checkout and certificate-issuance service in [`payments/`](payments/README.md) is built and tested: BTC orders with unique satoshi-offset amounts, an esplora/mempool.space chain watcher, minting at 1 confirmation, exactly-once license minting, key delivery by email with an order-status claim path, and automatic certificate issuance for clean exam results. **It is not yet processing live orders:** deployment on the owner's server is an owner step that has not happened yet. The site constants that wire the pages to it — `PAYMENTS_API_BASE` in `game/buy.html` and in `exam.html` — are currently empty, so the live buy page runs its interim mode (live CoinGecko $5 amount plus the manual fulfilment paths) and certificate countersigning runs through the manual tool route until deployment.
- **Owner-built — the premium pack.** Premium module bodies ship only as an AES-256-GCM encrypted pack. The pack is built locally by the owner with `tools/keygen.py build-pack` from the sources in `content/premium/`; it is never built in CI and its plaintext sources never ship in the app bundle. Premium unlock therefore depends on the owner-built pack being present in an edition — the app treats "pack not built yet" as a designed state with a plain status line, never as an error, and purchases and license keys stay valid across editions.

## Features — verified against this repository

- **46 modules in 7 tracks** (tables below), from scam defense for beginners through IT foundations, security operations, offensive security, systems and cloud, physical installs and safety, and professional pathways.
- **Free tier with no gate:** modules 01–03 are readable in the browser and in the app with no license and no account.
- **One curriculum standard:** every module carries learning objectives, case breakdowns, procedures, a hands-on exercise, a knowledge check with feedback, key takeaways, a glossary, official further reading, and a certification-alignment note.
- **90-question final exam:** question order and answer order are shuffled every attempt; pass mark is **80% — 72/90**; the exam is premium-gated and includes a full wrong-answer review with explanations.
- **Verifiable certificate:** passing generates a Sentinel Safeguard Certificate of Completion on the page instantly; the official countersigned certificate is Ed25519-based and anyone can check a countersigned certificate on the public [verify page](https://therealjesusthehacker.github.io/HackProof/verify.html).
- **Exam integrity layer:** behavioral signals (tab switches, window blurs, copy/cut/paste attempts, per-question timing, total duration) are computed locally in the browser and summarized into a clean/flagged verdict inside the certificate code. A clean verdict can be countersigned automatically by the payments service once it is deployed; a flagged verdict is **held for owner review and never auto-sent**. Signals are evidence, not proof — see [PRIVACY.md](PRIVACY.md) for exactly what is recorded and what is sent.
- **Offline license validation:** license keys are Ed25519-signed and wrap the premium content key. Validation happens on the student's device with public-key cryptography — no tracking, no phone-home, no account server.
- **Installable Windows app:** a single exe that is the app, the self-install engine, and the uninstaller. Install is an offer, never a gate; the course runs immediately, installed or not, and portable mode (data directory on a USB stick or folder) never installs at all.
- **No accounts, by design:** no usernames, no passwords, no login — in the app, on the site, or in the payments service. The license key is the account; the order ID is the claim credential for a paid key if the delivery email is lost.
- **Zero-collection posture:** the course collects nothing; see [PRIVACY.md](PRIVACY.md).

## The Course — 46 Modules, 7 Tracks

### Track 1 · Scam Defense Core
The original HackProof course: recognize and defeat the scams hitting your phone, inbox, family, and business.

| # | Module | Tier |
|---|--------|------|
| 01 | Spot the Phish | FREE |
| 02 | Smishing Basics | FREE |
| 03 | Tech Support Calls | FREE |
| 04 | Gift Card Scams | PREMIUM |
| 05 | QR Code Scams | PREMIUM |
| 06 | Crypto Scams | PREMIUM |
| 07 | Romance Scams | PREMIUM |
| 08 | Marketplace Scams | PREMIUM |
| 09 | Smishing Deep Dive | PREMIUM |
| 10 | Vishing Defense | PREMIUM |
| 11 | Passwords & 2FA | PREMIUM |
| 12 | AI & Deepfake Scams | PREMIUM |
| 13 | Account Takeover Defense | PREMIUM |
| 14 | Public Wi-Fi & Travel | PREMIUM |
| 15 | Already Got Scammed? | PREMIUM |
| 16 | Protecting Family | PREMIUM |
| 17 | Small Business Scams | PREMIUM |
| 18 | SIM Swap Defense | PREMIUM |
| 19 | Your Scam Radar | PREMIUM |
| 20 | AI Voice Clones: The Family Emergency Call | PREMIUM |
| 21 | Pig Butchering: The Long Investment Con | PREMIUM |
| 22 | Rental & Housing Scams | PREMIUM |
| 23 | Refund & Overpayment Scams | PREMIUM |
| 24 | Business Email Compromise | PREMIUM |
| 25 | Account Takeover Recovery: The First 24 Hours | PREMIUM |

### Track 2 · IT Foundations — *A+ · Network+ knowledge domains*
| # | Module |
|---|--------|
| 26 | Computer Hardware Essentials |
| 27 | Operating Systems & Troubleshooting |
| 28 | Networking Fundamentals |
| 29 | Network Operations & Troubleshooting |

### Track 3 · Security Core — *Security+ · CySA+ knowledge domains*
| # | Module |
|---|--------|
| 30 | Threats, Vulnerabilities & Cryptography |
| 31 | Identity, Access & Security Architecture |
| 32 | Security Operations & Incident Response |
| 33 | Threat Intelligence & Vulnerability Management |

### Track 4 · Offensive Security — *PenTest+ · CEH · eJPT domains; PNPT/OSCP readiness*
| # | Module |
|---|--------|
| 34 | Ethical Hacking Methodology |
| 35 | Exploitation & Post-Exploitation Basics |
| 36 | Pen Test Engagements: Reporting & Lab Strategy |

### Track 5 · Systems & Cloud — *Linux+ · CCNA · Azure · AWS knowledge domains*
| # | Module |
|---|--------|
| 37 | Linux System Administration Essentials |
| 38 | Routing & Switching Essentials |
| 39 | Cloud Foundations |
| 40 | Cloud Administration & Security |

### Track 6 · Physical Installs & Safety — *BICSI · ESA · manufacturer pathways; OSHA awareness*
| # | Module |
|---|--------|
| 41 | Structured Cabling & Physical Installs |
| 42 | Surveillance & Access Control Systems |
| 43 | Jobsite Safety, First Aid & Licensing Pathways |

### Track 7 · Professional Pathways — *the Sentinel credential standard*
| # | Module |
|---|--------|
| 44 | The Sentinel Credential Standard |
| 45 | Missouri Guard & PI Licensing Pathways |
| 46 | Leadership, Projects & Service Management |


**Start the course:** https://therealjesusthehacker.github.io/HackProof/

## Certification alignment — honestly

The tracks are built on the **Sentinel Safeguard Credential Standard** — the certification ladder Sentinel hires to (baseline A+/Network+/Security+; cyber CySA+, PenTest+, SecurityX, CEH, PNPT, eJPT, OSCP, GPEN/GWAPT, CISSP, CISM; systems Linux+/RHCSA, CCNA/CCNP, Azure, AWS; installs BICSI, ESA, manufacturer certs, OSHA 10; ASIS and Missouri licensing pathways for the future guard and PI divisions; PMP/ITIL 4 for leadership).

Every module carries a **Certification alignment** note naming the specific certifications and objective domains it supports. What alignment means — and doesn't:

- The course **teaches the knowledge domains these certifications test**, and builds toward them.
- The course **does not confer any certification or license**, and **never guarantees** passing an external exam. Vendor exams are taken separately through the certification body.
- Hands-on and state-issued credentials — BICSI installer levels, First Aid/CPR/AED, the OSHA 10 card, Missouri guard/PI licenses, firearms qualification — **cannot be granted by any online course**. Those modules teach the *pathway*: what each credential requires, who issues it, and how a Sentinel hire earns it.

## Who It's For

- **Everyday people** who want to stop getting scammed — seniors, parents, students, anyone with a phone and an inbox.
- **Aspiring IT and security professionals** building toward the Sentinel credential standard.
- **Small businesses** training staff against phishing, vishing, business email compromise, and social engineering.

## Get HackProof

### In the browser (free preview — start here)

Open **https://therealjesusthehacker.github.io/HackProof/** — the first 3 modules are free and run entirely in the browser, with no installation and no account.

### The Windows app (primary product form)

1. Download `HackProof.exe` and `SHA256SUMS.txt` from the **app-v1.0.5** release: https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.5
2. Verify the download (recommended): compare the SHA-256 of your `HackProof.exe` against `SHA256SUMS.txt` — in PowerShell, `Get-FileHash .\HackProof.exe -Algorithm SHA256`.
3. Run `HackProof.exe`. The course opens and works immediately — installation is not required to learn.
4. To install, accept the in-app install offer (or Settings → *Install / repair*): the same exe relaunches elevated, Windows shows its standard prompt, and HackProof places a byte-verified copy of itself at `C:\Program Files\Sentinel Safeguard\HackProof\HackProof.exe`, registers an Apps & Features entry, and adds a Start Menu shortcut — then verifies all three before claiming done. Uninstall runs from Apps & Features (`--uninstall`); your settings and saved license key are kept unless you tick the box to remove them.
5. Portable use: set the `HACKPROOF_DATA_DIR` environment variable to a folder and all app data lives there; in portable mode the app never installs. Full details in [app/README.md](app/README.md).

## Usage — the student and buyer flows

### Learn (free)

Open the site or the app and read modules 01–03. Progress is stored only on your own device.

### Unlock premium ($5 in Bitcoin)

Premium is a one-time **$5 USD in BTC**, bought on the buy page: https://therealjesusthehacker.github.io/HackProof/game/buy.html

- **Today (interim mode):** the buy page shows the live $5 equivalent in BTC (CoinGecko rate, BIP21 QR code) at the purchase address below, and fulfilment uses the manual paths described on the page and in [payments/README.md](payments/README.md).
- **Once the payments service is deployed (built and ready):** you enter an email, the service creates an order and assigns a **unique exact BTC amount** (the $5 base amount plus a small per-order satoshi offset — that exact amount is how a payment on the shared address is matched to your order), you pay exactly that amount from a wallet you control, the watcher sees it on-chain, and at **1 confirmation** exactly one license key is minted and emailed to you. If the email is lost, the order-status endpoint is the claim path: the order ID shows the key once the order is paid — so treat the order link like a receipt with a key printed on it.
- Either way, there are **no accounts**: the key itself is your account. Whoever holds the key holds the premium access, so keep it safe. Paste the key into the course (site or app) to unlock all 46 modules and the exam. Keys are validated offline on your device.

### Take the exam and earn the certificate

1. Finish the course with a premium license, then open the exam: https://therealjesusthehacker.github.io/HackProof/exam.html (or the Exam section in the app).
2. The exam is **90 questions** spanning the full course, shuffled on every attempt. **Pass at 80% (72/90).**
3. On a pass, your **Sentinel Safeguard Certificate of Completion** generates instantly on the page — print it or save it as PDF.
4. For the official countersigned certificate, submit your result as the exam page directs. The signed certificate is emailed to you; a clean integrity verdict is issued automatically once the payments service is deployed, and a flagged verdict is held for owner review rather than auto-sent. Until deployment, countersigning runs through the owner's manual tool (`tools/keygen.py sign-cert`) — the checks are identical either way.
5. Anyone can check a countersigned certificate at the verify page: https://therealjesusthehacker.github.io/HackProof/verify.html

## How It Works

- **The site** is a static GitHub Pages site in the Sentinel green/black design: the course catalog and reader (`game/index.html` — the path survives from an earlier product shape; the current product is the course), the buy page (`game/buy.html`), the final exam (`exam.html`), and the certificate verifier (`verify.html`) all run in the browser. Premium course content ships as an encrypted pack, unlocked by a license key.
- **The app** ([app/README.md](app/README.md)) is a PySide6 + Qt WebEngine shell that bundles the site at release time and serves it through a custom `hackproof://` scheme registered as a secure local scheme, so the course's WebCrypto pack decryption works exactly like HTTPS. One exe contains the app, the self-install/uninstall engine, and native buy/license screens. The unlocked course (free + premium) works fully offline; the network is used only for creating/polling an order and submitting a certificate, and there is no telemetry and no self-update — updates are delivered as new downloads.
- **License keys** are Ed25519-signed and wrap the premium content key (AES-256-GCM). The same key format is minted by the owner's `tools/keygen.py` and by the payments service, and each accepts the other's keys — the test suites prove that agreement in both directions. `tools/keygen.py` also builds the encrypted premium pack (`build-pack`) and countersigns certificates (`sign-cert`).
- **The payments service** ([payments/README.md](payments/README.md)) is a small Python service (standard library plus `cryptography`) that runs on the seller's own machine. It holds **no Bitcoin keys and cannot move funds** — it watches a public address on a public block-explorer API. Fulfilment is exactly-once by construction: a single conditional database update claims an order, so it cannot mint twice — not on a second poll, not after a restart, not if two watchers race. Problem payments (wrong amount, late, duplicate, exchange-batched) never auto-mint; they are logged for the owner's manual resolution.
- **Certificate issuance** validates a submission exactly like the manual `sign-cert` tool: score 72–90 of 90, percentage exactly consistent with the score, license binding, Ed25519-valid license, and HMAC proof. Clean integrity verdicts issue; flagged, missing, or unreadable verdicts fail closed to the owner's review hold. Issuance is idempotent — one certificate per license and exam pass.
- **Content protection** on course and exam pages (copy/selection deterrents) is a deterrent layer, not an absolute control — see `CHANGELOG.md` for the honest limits the project states for it.

### Repository layout

| Path | What it is |
|------|------------|
| `index.html` | Site entry / redirect to the course |
| `game/index.html` | Course catalog and reader (free modules in plaintext; premium from the encrypted pack) |
| `game/buy.html` | The premium buy page ($5 in BTC; interim mode until `PAYMENTS_API_BASE` is set) |
| `course/` | The free modules and micro-lessons as standalone Markdown |
| `content/premium/` | Premium module sources (04–46) and authoring notes — sources only, never shipped in plaintext |
| `exam.html` | The 90-question final exam + integrity layer |
| `verify.html` | Public certificate verification page |
| `shared.js` | Shared site logic, including the license public key |
| `app/` | The Windows app (PySide6 + Qt WebEngine) — see [app/README.md](app/README.md) |
| `payments/` | Automated BTC checkout + certificate issuance service — see [payments/README.md](payments/README.md) |
| `tools/keygen.py` | Owner tooling: license minting, premium pack building, certificate countersigning |
| `.github/workflows/build-app-windows.yml` | Release build for `app-v*` tags (test, build, smoke-test, attach assets) |

Further detail: [CHANGELOG.md](CHANGELOG.md) (release history), [app/README.md](app/README.md) (the Windows app), [payments/README.md](payments/README.md) (payments API contract and flows).

## Configuration

| Where | Name | What it does |
|-------|------|--------------|
| `game/buy.html` | `PAYMENTS_API_BASE` | Base URL of the payments service for order creation/status. Empty (`""`) in the repo today = interim mode on the live page. |
| `exam.html` | `PAYMENTS_API_BASE` | Base URL of the same service for automatic certificate delivery (`POST /api/certificates`). Empty = the manual countersigning route applies. |
| Windows app | `HACKPROOF_SERVICE_BASE_URL` | The same service base URL for the app; environment variable wins over the saved Settings value. |
| Windows app | `HACKPROOF_DATA_DIR` | Portable mode: all app data lives in that folder and the app never installs. |
| Windows app | `HACKPROOF_WEBROOT` | Bundle override for development. |
| Payments host | `~/.hackproof-payments/config.json` | The service's one JSON config file (price, address, confirmations, SMTP, admin token) — full reference in [payments/README.md](payments/README.md). |

## Development and Testing

Requirements: Python 3.10+ for the tooling and payments service; the app additionally needs PySide6 (see `app/packaging/requirements-ci.txt`).

```bash
# Owner tooling (license keys, premium pack, certificate countersigning)
python3 tools/keygen.py setup        # one-time: signing keypair + content key in ~/.hackproof
python3 tools/keygen.py mint --tier premium --days 365
python3 tools/keygen.py build-pack   # encrypt content/premium into the premium pack
python3 tools/keygen.py sign-cert --license <student key> <certificate code>

# Payments service
python3 -m unittest discover -s payments/tests -v   # 32 tests, network stubbed
python3 payments/service.py --selftest               # dress rehearsal: no network, no money
python3 payments/service.py --check                  # validate config + key store

# Windows app
python app/tools/bundle_site.py      # site tree -> app/build/webroot
python -m pytest app/tests -q        # 111 test functions across 11 files (see app/README.md)
```

The payments suite (32 tests) stubs CoinGecko, the esplora API, and SMTP, and proves — against the real `tools/keygen.py` — that service-minted and keygen-minted keys accept each other, that 1 confirmation mints exactly once (including across restarts), and that the certificate accept/refuse matrix matches `sign-cert` exactly. The app suite covers Ed25519 verification against the real keygen, license refusals, the install state machine, the bundler, the service client and proxy shim, and headless GUI tests. Release builds additionally run both exe self-checks (`--self-check`, `--self-check-qt`) in the workflow before any asset is attached.

## Status and Roadmap

- **Now:** website live; Windows app at **app-v1.0.5**; course at 46 modules / 7 tracks; exam and verifiable certificate in place.
- **Next owner step:** deploy the payments service on the owner's server and set `PAYMENTS_API_BASE` on the buy and exam pages, which switches fulfilment and certificate delivery from the interim/manual paths to the automated flow described above.
- **Ongoing:** course and app maintenance under the project's build → audit → fix → re-audit cycle; per-release history is recorded in [CHANGELOG.md](CHANGELOG.md).

## Support the Project

HackProof is independent security education — no investors, no ads, no data to sell. If it helped you, tip the mission:

```
bc1qvydns2fmyjzj55wzxq7ta28nxdhcmu9l9m6yg0
```

Copy it character-for-character. Every donation goes back into building more training. (This is also the purchase address used by the buy page.)

## Contact

Questions, license issues, bulk/business licensing: **Sentinelsafeguard@outlook.com**

## License and Legal

HackProof is proprietary commercial software and content — see [LICENSE](LICENSE) (Copyright (c) 2026 JesusTheHacker; exclusive property of JesusTheHacker / Sentinel Safeguard LLC). Purchasing premium grants a personal, non-transferable license to use the premium content; no copying, redistribution, resale, or derivative works without prior written permission.

- [LICENSE](LICENSE) — proprietary commercial license
- [TERMS.md](TERMS.md) — terms of use
- [PRIVACY.md](PRIVACY.md) — privacy policy (tl;dr: the course collects nothing)
- [SECURITY.md](SECURITY.md) — report vulnerabilities

Copyright (c) 2026 JesusTheHacker. All rights reserved.
