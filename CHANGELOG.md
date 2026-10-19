# HackProof Changelog

All notable changes to HackProof are documented here.

## [Unreleased]

### Fixed (2026-10-19 hardening sweep)
- `tools/keygen.py mint` now validates `--days` (1–3650) — a 0/negative value previously minted a license that was already expired on arrival
- Game: a remembered license is no longer wiped at boot when only the premium pack fails to load (e.g. pack not deployed yet) — the key stays saved if the license itself still verifies; only genuinely bad/expired keys are forgotten
- Game: all scenario / premium-pack / manifest text is HTML-escaped at render time (defense-in-depth; the content carries no intended HTML)
- Exam: added a `beforeunload` warning while an attempt is in progress, and a fail-closed check that the question bank is exactly 90 questions (the fixed protocol shared with `sign-cert`)
- Verifier: unsigned certificate codes now show only the certificate ID — holder/score fields in an unsigned payload are unauthenticated and are no longer rendered
- Removed dead `S.pending` state from the game

### Added
- **Final exam** (`exam.html`) — 90 questions across all 19 modules, shuffled order + shuffled options per attempt, 80% (72/90) pass threshold, premium-gated, full wrong-answer review with explanations
- **Verifiable certificate** — auto-generates on passing with the student's name (entered at exam start); printable one-page certificate under the Sentinel Safeguard LLC name; Ed25519-countersigned verification codes via `tools/keygen.py sign-cert`
- **Certificate verifier** (`verify.html`) — offline cryptographic verification of countersigned certificates; unsigned codes show as pending
- `README.md` — full product documentation: game overview, 19-module course outline, premium pricing
- `LICENSE` — proprietary commercial license
- `SECURITY.md` — vulnerability reporting policy and license-key crypto overview
- GitHub issue templates (bug report, feature request) and pull request template
- `.gitignore` — OS/editor junk, dependency dirs, key material, premium pack sources

## [1.0.0] — 2026-10-11

### The launch
- **"YOU ARE THE SCAMMER" game** (`game/index.html`) — single-player browser game: play the villain to learn defense. 8 scam scenarios, lure-vs-heat scoring, defense briefs after every scenario, ranks from SCRIPT KIDDIE to KINGPIN. Free tier (first 3 scenarios) + encrypted premium pack unlocked by license key.
- **Buy page** (`game/buy.html`) — premium purchase page: $5 in BTC with live CoinGecko rate and BIP21 QR.
- **License tooling** (`tools/keygen.py`) — Ed25519 license minting and premium pack builder (AES-256-GCM).
- **Course** (`course/`) — 3 free full modules (01-passwords-mfa, 02-phishing, 03-social-engineering) + 3 micro-lessons (spot-the-phish, smishing-basics, tech-support-calls). Premium modules 04–19 ship encrypted in the premium pack.
- **Root redirect** (`index.html`) → the game on GitHub Pages.
- **TERMS.md** and **PRIVACY.md** — plain-language terms and zero-collection privacy policy.
