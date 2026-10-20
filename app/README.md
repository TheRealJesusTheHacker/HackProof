# HackProof — the Windows app

[![App release](https://img.shields.io/github/v/release/TheRealJesusTheHacker/HackProof?filter=app-v*&style=flat-square&label=app%20release)](https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.4)
[![App build](https://img.shields.io/github/actions/workflow/status/TheRealJesusTheHacker/HackProof/build-app-windows.yml?style=flat-square&label=app%20build)](https://github.com/TheRealJesusTheHacker/HackProof/actions/workflows/build-app-windows.yml)
[![License: PROPRIETARY](https://img.shields.io/badge/license-PROPRIETARY-red?style=flat-square)](../LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)](https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.4)

The installable Windows edition of HackProof — the primary product form.
Current release: **app-v1.0.4** (assets: `HackProof.exe` + `SHA256SUMS.txt`).
Product overview, course tables, and pricing live in the [root README](../README.md);
the payments service the app talks to is documented in [payments/README.md](../payments/README.md).

## Download, verify, run

1. Download `HackProof.exe` and `SHA256SUMS.txt` from the app-v1.0.4 release:
   https://github.com/TheRealJesusTheHacker/HackProof/releases/tag/app-v1.0.4
2. Verify the exe before running it (recommended): in PowerShell,
   `Get-FileHash .\HackProof.exe -Algorithm SHA256`, and compare the result
   with `SHA256SUMS.txt`.
3. Run `HackProof.exe`. The course opens immediately — installation is an
   offer, never a gate (details below). `--version` prints the app version.

## What a student sees

The main window is a navigation shell with six sections — **Course**,
**My Premium**, **Exam**, **Verify**, **Settings**, and **About**:

- **Course** — the full course catalog and reader (the bundled website,
  served inside the app). Modules 01–03 are free; premium modules unlock
  with a license key. The unlocked course works fully offline.
- **My Premium** — native buy and license screens: enter a license key to
  unlock, or run the purchase flow against the payments service when a
  service base URL is configured. If the premium pack has not been built
  into an edition yet, this screen says so in plain language — that is a
  designed state, not an error (see *Premium pack states* below).
- **Exam** — the 90-question final exam (pass at 72/90), with the same
  integrity layer as the web exam.
- **Verify** — check a countersigned certificate code.
- **Settings** — the service base URL, install / repair, and the saved
  license key.
- **About** — version, pack state, and the plain statement of the app's
  network posture: no telemetry, no self-update; updates are delivered
  as new downloads.

One `HackProof.exe` is the whole product (the ARGUS.EXE pattern):
the course app, the self-install engine, and the setup/uninstall
flows, routed at launch by `hackproof_app/entry.py`.

- **Run it** → the app opens. The course works immediately,
  installed or not.
- **Install is an offer, never a gate** (a course needs nothing
  privileged): a dismissible banner — or Settings → *Install /
  repair* — relaunches the same exe elevated (`--run-setup`),
  Windows shows its one familiar prompt, and HackProof places a
  byte-verified copy of itself at
  `C:\Program Files\Sentinel Safeguard\HackProof\HackProof.exe`,
  registers an Apps & Features entry, adds a Start Menu shortcut,
  and verifies all three before claiming done. Partial installs
  are detected (`INSTALLED_INCOMPLETE`) and healed by re-running.
- **`--uninstall`** (what the Apps & Features entry points at)
  self-elevates, confirms in plain language, and removes the
  program, shortcut, and entry. The person's data (settings +
  saved license key) is kept unless they tick the box to remove
  it; a running exe's own file is scheduled for deletion at
  restart and reported as a leftover, never hidden.
- **`--self-check` / `--self-check-qt`** are the release
  pipeline's smoke tests (import census; real window + web view
  construction, offscreen). `--version` prints the version.

## Layout

```
app/
  hackproof_app/
    entry.py          launch routing + self-checks
    config.py         data dirs, settings, the shared service-URL config
    license_keys.py   pure-Python Ed25519 license verification (stdlib only)
    service_client.py typed client for the payments service contract
    proxy_logic.py    pure /api proxy logic + the certificate shim
    site_bundle.py    finds the bundled website + reads its manifest
    setup_engine.py   the self-install/uninstall state machine
    gui/
      theme.py        Sentinel green/black theme (zero purple)
      app.py          GUI bootstrap (scheme first, then windows)
      main_window.py  nav shell: Course / My Premium / Exam / Verify /
                      Settings / About + the install banner
      webview.py      hackproof:// scheme handler (site + /api proxy),
                      copy-protection reinforcement, license seeding
      premium_page.py native buy + license screens
      setup_app.py    setup/uninstall progress dialogs (close-hardened)
      assets/         qr.html/js (clean-room QR encoder), md reader,
                      not-found page, app icon
  tools/
    bundle_site.py    build-time: site tree -> build/webroot + manifest
    make_icon.py      generates the icon (PNG asset + .ico)
  packaging/
    HackProof.spec    PyInstaller one-file build (version resource incl.)
    launch_hackproof.py
    requirements-ci.txt
  tests/              the suite (see below)
.github/workflows/build-app-windows.yml   the release build (repo root)
```

## Rendering engine: Qt WebEngine (chosen on evidence)

The course is the website: heavy JS, WebCrypto pack decryption,
and an exam whose integrity layer reads `visibilitychange`/blur.
Two candidates were weighed:

- **System WebView2 via pywebview** — smaller download, but the
  app would depend on a runtime the customer may not have (the
  bootstrapper becomes a second installer that can fail), Edge
  updates change the engine under the product, and a custom
  scheme with guaranteed secure-context treatment is
  WebView2-specific plumbing.
- **Qt WebEngine (chosen)** — ships inside the exe (no runtime to
  install, ever), the `hackproof://` scheme is registered as a
  secure local scheme so WebCrypto works exactly like HTTPS, the
  whole shell is one vendor (PySide6 — the kit's stack), and the
  CI `--self-check-qt` gate constructs a real web view from the
  built exe. Cost: roughly +180 MB in the one-file bundle. For a
  flagship course product, reliability won over size.

Stacked-widget navigation gives the exam its semantics for free:
leaving the Exam section hides its web view, which is exactly
the `visibilitychange` the integrity layer counts, and window
deactivation blurs natively.

## Build

Local development (any platform with PySide6):

```
python app/tools/bundle_site.py           # site tree -> app/build/webroot
python -m pytest app/tests -q             # the suite
PYTHONPATH=app python app/packaging/launch_hackproof.py   # run the app
```

Release (Windows, what CI does on an `app-v<version>` tag):

```
pip install -r app/packaging/requirements-ci.txt
python app/tools/bundle_site.py
python -m pytest app/tests -q
pyinstaller app/packaging/HackProof.spec --noconfirm   # -> dist/HackProof.exe
```

Release assets: **`HackProof.exe`** (the exe is both installer
and app — a "Setup" name would lie after installation) and
**`SHA256SUMS.txt`**. The workflow checks the tag against
`hackproof_app.__version__`, greps the PyInstaller warn file for
the lazy-import watchlist (QtWebEngine above all), and runs both
self-checks against the built exe before uploading.

The bundler copies the **site tree at release time** — app
content is never forked into `app/**`. It excludes owner tooling
(`tools/`), the payments service (`payments/` — a server
component), the premium pack **sources** (`content/` — premium
ships only as ciphertext), and repository plumbing. From
`game/` it ships only `index.html` — that page IS the course
catalog and reader — while the web buy page stays out (buying
happens natively in the app; in-app links to it are rewritten
to an in-app guidance page). The built pack artifact, when
present, still ships. The bundler rewires the bundled copies'
service constants to the app origin, applies the Sentinel
brand pass to the copies (the site's purple design tokens
become the app's greens — the app ships zero purple), and
writes `app-manifest.json` (pages present, pack state,
free-module list, the license public key read from `shared.js`,
what was rewired, warnings). The repo's own files are never
modified.

## Contracts consumed

- **License keys** (owner tooling: `tools/keygen.py`; site:
  `shared.js`). Key = base64(JSON `{id, tier, expiry, S,
  wrapped_Kc, sig}`); Ed25519 over the canonical fields. The app
  verifies with a stdlib-only RFC 8032 implementation in
  `license_keys.py`, reusing the site's exact refusal wording and
  its clock-rollback guard. The public key comes from the bundle
  manifest (extracted from `shared.js` at bundle time) — it is
  never duplicated into app source. Tests prove agreement with
  the real keygen (setup + mint + verify + tamper refusals).
- **Payments service** (`payments/`): `POST /api/orders {email}`
  → order with exact BTC amount/address; `GET /api/orders/<id>`
  (paid orders reveal the key — the order id is the claim
  credential); `POST /api/certificates {email, license_key,
  certificate_code, integrity}` → `issued` / `held_for_review`;
  `GET /healthz`. `service_client.py` is a typed client over an
  injectable transport; every error is two-voice (plain
  `user_message` for screens, `detail` for logs).
- **Pages in-app**: bundled pages talk to `hackproof://app/api/…`
  and the scheme handler proxies to the configured service.
- **Configuration — one shared name**: the service base URL is
  the `HACKPROOF_SERVICE_BASE_URL` environment variable when set,
  else the saved setting (Settings screen). The site's page
  constant is `CERT_SERVICE_BASE_URL` (in repo files it stays
  `""`; only bundled copies are rewired). Other env vars:
  `HACKPROOF_DATA_DIR` (portable mode: all data in that folder,
  never installs), `HACKPROOF_WEBROOT` (bundle override).

### The certificate compatibility shim (documented, deliberate)

The exam page's submission and the service's contract currently
differ in three ways (found while building this app):
(1) the page nests `integrity` inside its `payload`; the service
reads a top-level `integrity` and fail-closes to a hold without
one; (2) the page sends no `license_key`; the service requires
it for the HMAC proof; (3) the service answers
`held_for_review`; the page checks for `held`. `proxy_logic.py`
bridges all three inside the app only, never overriding a field
the sender provided. The durable fix belongs to the site/service
crews; when they converge the shim becomes a no-op. **Current
tree note:** today's `exam.html` carries no service endpoint
constant at all (it produces the signed certificate code for the
manual route), so the bundler warns at build time and in-app
automatic delivery lights up when the page wiring lands — the
proxy, client, and tests are already in place.

### Premium pack states

The pack is built by the owner locally (`keygen build-pack`).
The manifest reports `built` / `not-built` / `absent`; the app
treats "not built yet" as a designed state (status line in My
Premium and About), never an error. Purchases and keys stay valid
across editions.

## Offline posture

The course (free modules + unlocked premium) works fully
offline. Network is used only for: creating/polling an order and
submitting a certificate (the payments service) — and nothing
else. There is no telemetry and no self-update in v1; the About
screen says so plainly ("updates are delivered as new
downloads"). The version constant lives in
`hackproof_app/__init__.py` for when updates land.

## Tests

```
python -m pytest app/tests -q
```

89 test functions across eight files (pytest collects more cases than
function names — the entry-routing test alone is parametrized over
eight invocations): Ed25519 (RFC vectors, cross-implementation agreement,
real-keygen interop), license refusals (tamper/expiry/clock),
canonical-bytes equality with keygen, service client against the
stubbed contract, proxy shim normalization, config
round-trip/corruption/env precedence, the install state machine
(injected seams: happy path, resumable failure, uninstall
data-keeping, result hand-off), entry routing + self-check
seams, the bundler (exclusions, rewiring, pack states, manifest),
and headless GUI tests (theme discipline — no purple, nav
gating, designed degradation when the browser component is
unavailable, the full buy flow to a saved key, key unlock/refusal,
setup-dialog close-hardening). `cryptography` is a test-only
dependency (CI installs it; the app itself is stdlib + PySide6).

Linux note: the GUI tests run headless (`QT_QPA_PLATFORM=offscreen`);
this VM also needs its Qt runtime libs on `LD_LIBRARY_PATH` and
cannot load QtWebEngine (missing system libXtst) — the suite is
built so that path is the designed-degradation test, and Windows
CI is the real WebEngine gate via `--self-check-qt`.

Windows-only verification (for the first Windows run): the
install flow end to end (UAC prompt, ARP entry, shortcut,
self-verification), WebEngine rendering of the real exam,
focus/blur → `visibilitychange` counting, Ctrl+C inertness in
course pages with Paste live, the payment QR scanning to the
right BIP21 string, proxy POST body forwarding against a stub
service, and the release tag/version gate.

## Status

- **app-v1.0.4** is the current release. The release workflow
  (`.github/workflows/build-app-windows.yml`, at the repo root) runs only
  for `app-v*` tags, checks the tag against `hackproof_app.__version__`,
  runs this suite, builds the exe, greps the PyInstaller warn file for
  the lazy-import watchlist, and runs both self-checks against the built
  exe before attaching `HackProof.exe` and `SHA256SUMS.txt`.
- Buying and automatic certificate delivery inside the app light up when
  a payments-service base URL is configured; the service itself is built
  and ready, and its deployment on the owner's server is the remaining
  owner step (see the root README's status section). Everything else —
  the course, the exam, offline license validation, the manual
  certificate route — works without it.

## License

Proprietary — see [LICENSE](../LICENSE) at the repo root. Purchasing
premium grants a personal, non-transferable license to use the premium
content; no copying, redistribution, resale, or derivative works
without prior written permission. Questions and bulk/business
licensing: **Sentinelsafeguard@outlook.com**.
