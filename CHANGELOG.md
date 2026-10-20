# HackProof Changelog

All notable changes to HackProof are documented here.

## [Unreleased]

### Added (2026-10-20 promo / test access codes)
- **Promo / test access codes (app only)** — a short code unlocks premium in the Windows app with no purchase and no contact with the payments service. The promo is built into the owner's key tool: `tools/keygen.py` carries the code in concealed (sealed) form — never in plaintext in this repo, the website, or the app — and every `build-pack` derives a real promo license from it, publishing signed metadata (`app/promo-meta.json`, bundled into the app) from which the app re-derives the license from the entered code (PBKDF2-HMAC-SHA256, per-build salt) and verifies it against the signing key before unlocking. A wrong code fails like a forged key, repeated failures back off from 5 seconds up to 5 minutes (persisted across restarts), and an unlocked promo session is labeled **"Premium — promo access"**. Certificates earned under a promo unlock are countersigned by the same `sign-cert` rules as purchased ones. Rotating the code means updating the sealed built-in in the tooling and rebuilding the pack; retiring it means removing the built-in and rebuilding — editions built without it ship the metadata as `null` and the promo card shows a plain not-active note. The website is not part of this feature and is unchanged by it.
- **Windows app v1.0.3** — adds the My Premium promo / test code card, plus a tighter My Premium layout so the payment panel keeps its guarded spacing with the new card present.

### Changed (2026-10-19 course expansion)
- **Course expanded to 46 modules across 7 tracks**, all built to one enterprise curriculum template: learning objectives, prerequisites/level, lessons with worked case breakdowns, a hands-on exercise, a knowledge check with answer feedback, key takeaways, a glossary, further reading, and a **certification alignment** note. Track 1 (Scam Defense Core) gained AI Voice Clones (20), Pig Butchering (21), Rental & Housing Scams (22), Refund & Overpayment Scams (23), Business Email Compromise (24), and Account Takeover Recovery (25). New cert-mapped tracks: IT Foundations (26–29, A+/Network+ domains), Security Core (30–33, Security+/CySA+), Offensive Security (34–36, PenTest+/CEH/eJPT + PNPT/OSCP readiness), Systems & Cloud (37–40, Linux+/CCNA/Azure/AWS), Physical Installs & Safety (41–43, BICSI/ESA/OSHA pathways), Professional Pathways (44–46, the Sentinel credential standard, Missouri guard/PI licensing pathways, ASIS, PMP/ITIL orientation). Alignment means the course teaches the knowledge domains those certifications test — it confers no certification or license, and hands-on/state-issued credentials are taught as pathways. The three long-form modules and three micro-lessons under `course/` were expanded to the same standard.
- **The game is removed from the live product** ("YOU ARE THE SCAMMER" scenarios, ranks, and game framing) — the product is the course now. Free tier = modules 01–03; premium = all 46 modules + the final exam. The premium pack is course-only (43 premium modules). Game code remains recoverable in git history.
- **The course is becoming an installable Windows app** (in development): the web assets stay self-contained and offline-safe for the app shell, and this Pages site serves as the landing/download front door, the public certificate verify page, and the free web preview.
- **Buy page — automated fulfillment, wired to the payments service contract** (`payments/README.md`): enter email → create an order → the service assigns a unique exact BTC amount → pay from a wallet you control → payment detected on-chain automatically → license key generated and emailed automatically at 1 confirmation. No accounts — the key itself is the account, and the order ID is the claim credential (the status checker shows the key once paid). Wrong-amount/exchange payments fall back to manual resolution by transaction ID, as before. One configurable constant (`PAYMENTS_API_BASE` in `game/buy.html`) wires the service; until it is set, the page runs an interim mode (live CoinGecko amount + the manual paths).
- **Copy protection** on course content and exam questions: text selection disabled, copy/cut intercepted with a polite notice, context menu and drag suppressed on protected content. A deterrent layer (not absolute — view-source and screenshots can't be prevented on the web); certificates, form fields, and paste-into-license-key are unaffected.
- **Exam integrity monitoring:** local behavioral signals (tab switches, window blurs, copy/cut/paste attempts, per-question timing, total duration) summarized into a clean/flagged verdict embedded in the certificate payload. `tools/keygen.py sign-cert` surfaces the verdict prominently and warns when flagged — the seller decides; genuine certificates validate exactly as before (score 72–90, percentage consistency, license binding unchanged).
- **Certificate email delivery:** on a pass, the exam page submits the certificate code + license key (required to verify the code's proof) + integrity block to the service (`PAYMENTS_API_BASE` in `exam.html` → `POST /api/certificates`). Clean verdicts are countersigned and emailed automatically, and the returned countersigned code lights the verified seal on the page; flagged verdicts return "held for review" and the student sees a calm review message (never an accusation). The on-page certificate remains the instant copy; the manual email route remains available.
- README, TERMS, and PRIVACY rewritten course-only with true counts; PRIVACY documents the integrity signals and the automated purchase/certificate flows.

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
