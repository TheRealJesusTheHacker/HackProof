# HackProof Changelog

All notable changes to HackProof are documented here.

## [Unreleased]

### Added
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
