#!/usr/bin/env python3
"""Bundle the HackProof website into the app's webroot.

Run at build time (the release workflow runs it before
PyInstaller; a developer can run it to make ``app/build/webroot``
for a local GUI run):

    python app/tools/bundle_site.py [--repo PATH] [--out PATH]

What it does, and why:

- **Copies the site tree** (the repository root IS the website)
  into the webroot, minus everything that must never ship inside
  the app: owner tooling (``tools/``), the payments service
  (``payments/`` — a server component, not app content), the app
  itself (``app/``), repository plumbing (``.git``, ``.github``),
  and the premium pack SOURCES (``content/`` — premium ships only
  as the encrypted pack, never as readable lessons). Of the
  ``game/`` folder only ``index.html`` ships: it IS the course
  catalog and reader (the scam game itself was removed from the
  product; the folder kept the name). The website's buy page
  (``game/buy.html``) does NOT ship — buying inside the app is the
  native My Premium screen, and links to the buy page in bundled
  copies are rewritten to an app page that says exactly that.
- **Rewires the service constants** in the bundled copies only:
  the pages' ``CERT_SERVICE_BASE_URL`` (and any sibling
  ``*_BASE_URL`` / ``*_STATUS_ENDPOINT`` / ``*_API_BASE``
  constant — the exam page's is ``PAYMENTS_API_BASE``) is pointed
  at the app origin ``hackproof://app`` so in-app page requests
  land in the app's proxy, which forwards them to the service
  base URL from the app's Settings. Repository files are never
  touched.
- **Applies the Sentinel brand palette** to the bundled copies:
  the website's pages are designed in a purple palette; the app
  is a Sentinel Safeguard product and ships green-on-black only
  (the owner's standing brand rule — no purple anywhere). A fixed
  token map (:data:`BRAND_MAP`) rewrites the purple design tokens
  to their Sentinel green equivalents in the bundled copies only.
  Page content, layout, and wording are untouched; the website
  itself keeps its own design.
- **Detects the premium pack**: a built pack (ciphertext inlined
  behind the ``/*__PREMIUM_PACK__*/`` marker, or a
  ``premium-pack.b64`` artifact) means premium can unlock in this
  edition; the empty marker means the owner's local pack build
  hasn't run — the app shows that as a designed state, not a
  failure.
- **Writes ``app-manifest.json``** into the webroot: pages
  present, pack state, free-module list, the license public key
  read from ``shared.js``, what was rewired, and warnings the
  release notes should know about.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hackproof_app.license_keys import public_key_hex_from_shared_js  # noqa: E402
from hackproof_app.proxy_logic import APP_ORIGIN  # noqa: E402
from hackproof_app.site_bundle import (  # noqa: E402
    PACK_ABSENT,
    PACK_BUILT,
    PACK_NOT_BUILT,
)

EXCLUDED_DIRS = {
    ".git", ".github", "app", "payments", "tools", "content",
    "__pycache__", "node_modules",
}
#: Under game/ only the course page ships (see the module
#: docstring): index.html is the catalog + reader; buy.html is
#: replaced by the app's native My Premium screen.
GAME_SHIPPED = {"index.html"}
EXCLUDED_SUFFIXES = {".py", ".pyc", ".pyo"}
PACK_MARKER = "/*__PREMIUM_PACK__*/"
CONST_PATTERN = re.compile(
    r"((?:const\s+)?[A-Z][A-Z0-9_]*(?:BASE_URL|STATUS_ENDPOINT|API_BASE)"
    r"\s*=\s*\")[^\"]*(\")"
)

#: Links to the website's buy page, in every form the pages use
#: (plain and JS-escaped, from the root pages and from game/).
BUY_LINK_PATTERN = re.compile(
    r"(href=(?:\\?[\"']))(?:game/)?buy\.html"
)
BUY_LINK_TARGET = "/_app/buy-in-app.html"

#: The Sentinel brand pass: the site palette's purple design
#: tokens -> the Sentinel green equivalents the app chrome uses
#: (hackproof_app.gui.theme). Role-preserving: page backgrounds
#: stay near-black, cards stay cards, the bright accent stays the
#: accent, text stays text — only the hue family changes. The
#: certificate's purple on its cream stock becomes the deep
#: green a certificate seal traditionally wears. Functional
#: colors (danger reds, warning gold, success greens, the cream
#: certificate stock itself) are NOT in this map and never move.
BRAND_MAP = {
    # page backgrounds (purple-black -> green-black)
    "#0a0612": "#060a07",
    "#100a1c": "#060a07",
    "#0d0718": "#060a07",
    "#140c24": "#060a07",
    "#150b26": "#060a07",
    "#120a1e": "#0a120b",
    "#120a1f": "#0a120b",
    "#1d0f38": "#0a120b",
    # cards and raised surfaces
    "#170d28": "#0c130d",
    "#1a0f2e": "#0c130d",
    "#1c1530": "#0c130d",
    "#1c0f33": "#0c130d",
    "#1d1030": "#0c130d",
    "#241538": "#0c130d",
    "#221338": "#111a12",
    "#221239": "#111a12",
    "#241641": "#16251a",
    "#2a1650": "#14532d",
    # hairlines and deep-purple fills
    "#241536": "#1e3323",
    "#2c1847": "#1e3323",
    "#3b2163": "#1e3323",
    "#4a2a7a": "#14532d",
    "#4c1d95": "#14532d",
    "#6d28d9": "#14532d",
    # the purple accents themselves
    "#7c3aed": "#14532d",
    "#a855f7": "#1e7a3c",
    "#c084fc": "#2ee06f",
    "#d8b4fe": "#8fd6a4",
    # purple-grey text tones -> the theme's text tones
    "#9d8bb5": "#9db3a4",
    "#9d8fb8": "#9db3a4",
    "#8a7fa8": "#9db3a4",
    "#5b5470": "#7d927f",
    "#3d3654": "#2f4536",  # muted text on the cream certificate
    "#efe8fa": "#e8f2ea",
    "#f3efff": "#e8f2ea",
    "#e6dcf7": "#e8f2ea",
    "#e8e2f5": "#e8f2ea",
}
#: rgba() form of the primary purple (glow shadows in the pages).
BRAND_RGBA_FROM = "168,85,247"
BRAND_RGBA_TO = "30,122,60"  # #1e7a3c, the mapped --purple
_BRAND_HEX_PATTERN = re.compile(
    "(" + "|".join(re.escape(k) for k in BRAND_MAP) + ")"
    r"([0-9a-fA-F]{2})?(?![0-9a-fA-F])",
    re.IGNORECASE,
)


def _iter_site_files(repo: Path):
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] == "game" and (
            len(rel.parts) != 2 or rel.parts[1] not in GAME_SHIPPED
        ):
            continue
        if path.is_dir():
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield rel, path


def copy_site(repo: Path, out: Path) -> list[str]:
    # Every repo-relative path this module reports — the copied
    # list, the manifest's fields, the rewired/brand/buy-link
    # records — is POSIX-normalized (.as_posix()). The manifest
    # is a product surface produced on the build machine and read
    # on every platform; a Windows build must not leak
    # backslashes into it.
    copied: list[str] = []
    for rel, src in _iter_site_files(repo):
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        copied.append(rel.as_posix())
    # The built pack artifact lives under game/ today (keygen's
    # build-pack writes game/premium-pack.b64); ship the ciphertext
    # even though the game's pages are excluded.
    pack_file = repo / "game" / "premium-pack.b64"
    if pack_file.is_file():
        shutil.copyfile(pack_file, out / "premium-pack.b64")
        copied.append("premium-pack.b64")
    return copied


def _text_files(out: Path) -> list[Path]:
    return (
        sorted(out.rglob("*.html"))
        + sorted(out.rglob("*.js"))
        + sorted(out.rglob("*.css"))
    )


def rewire_constants(out: Path) -> list[str]:
    """Point the bundled pages' service constants at the app
    origin. Returns the list of "file:CONST" rewired."""
    rewired: list[str] = []
    for path in _text_files(out):
        text = path.read_text(encoding="utf-8", errors="replace")

        def _sub(match: re.Match) -> str:
            name = re.search(r"([A-Z][A-Z0-9_]*)\s*=", match.group(0))
            rewired.append(
                f"{path.relative_to(out).as_posix()}:"
                f"{name.group(1) if name else 'CONST'}"
            )
            return match.group(1) + APP_ORIGIN + match.group(2)

        new = CONST_PATTERN.sub(_sub, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
    return rewired


def rewrite_buy_links(out: Path) -> list[str]:
    """Point links to the website's buy page at the app's own
    guidance page (buying in-app is the native My Premium
    screen). Returns the list of files rewritten."""
    touched: list[str] = []
    for path in _text_files(out):
        text = path.read_text(encoding="utf-8", errors="replace")
        new, n = BUY_LINK_PATTERN.subn(
            lambda m: m.group(1) + BUY_LINK_TARGET, text
        )
        if n:
            path.write_text(new, encoding="utf-8")
            touched.append(path.relative_to(out).as_posix())
    return touched


def _brand_sub(match: re.Match) -> str:
    return BRAND_MAP[match.group(1).lower()] + (match.group(2) or "")


def apply_brand_theme(out: Path) -> dict[str, int]:
    """Apply :data:`BRAND_MAP` to the bundled copies (the app
    ships Sentinel green-on-black; the website keeps its own
    palette). Returns {file: replacement_count} for the files
    that changed."""
    counts: dict[str, int] = {}
    for path in _text_files(out):
        text = path.read_text(encoding="utf-8", errors="replace")
        new, n_hex = _BRAND_HEX_PATTERN.subn(_brand_sub, text)
        n_rgba = new.count(BRAND_RGBA_FROM) + new.count(
            BRAND_RGBA_FROM.replace(",", ", ")
        )
        new = new.replace(BRAND_RGBA_FROM, BRAND_RGBA_TO)
        new = new.replace(
            BRAND_RGBA_FROM.replace(",", ", "),
            BRAND_RGBA_TO.replace(",", ", "),
        )
        if new != text:
            path.write_text(new, encoding="utf-8")
            counts[path.relative_to(out).as_posix()] = n_hex + n_rgba
    return counts


def detect_pack(out: Path) -> tuple[str, int]:
    """(state, ciphertext_bytes) for the premium pack."""
    total = 0
    built = False
    marker_seen = False
    pack_b64 = out / "premium-pack.b64"
    if pack_b64.is_file():
        size = len(pack_b64.read_text(
            encoding="utf-8", errors="replace").strip())
        if size > 0:
            built = True
            total += size
    for path in list(out.rglob("*.html")) + list(out.rglob("*.js")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            re.escape(PACK_MARKER) + r"\s*\"([^\"]*)\"", text
        ):
            marker_seen = True
            if match.group(1):
                built = True
                total += len(match.group(1))
    if built:
        return PACK_BUILT, total
    if marker_seen:
        return PACK_NOT_BUILT, 0
    return PACK_ABSENT, 0


def collect_modules(out: Path) -> list[dict]:
    modules: list[dict] = []
    course = out / "course"
    if course.is_dir():
        for path in sorted(course.rglob("*")):
            if path.suffix == ".md":
                modules.append(
                    {"path": path.relative_to(out).as_posix(),
                     "kind": "markdown"}
                )
            elif path.suffix == ".html":
                modules.append(
                    {"path": path.relative_to(out).as_posix(),
                     "kind": "page"}
                )
    return modules


def build_manifest(repo: Path, out: Path, copied: list[str],
                   rewired: list[str], brand: dict | None = None,
                   buy_links: list[str] | None = None) -> dict:
    warnings: list[str] = []
    pages = {
        "course": (out / "index.html").is_file(),
        "exam": (out / "exam.html").is_file(),
        "verify": (out / "verify.html").is_file(),
    }
    for key, label in (("course", "index.html"), ("exam", "exam.html"),
                       ("verify", "verify.html")):
        if not pages[key]:
            warnings.append(f"{label} missing from the site tree")
    if pages["exam"] and not any(
        r.startswith("exam.html:") for r in rewired
    ):
        warnings.append(
            "exam.html service constant not rewired — in-app "
            "certificate delivery falls back to the page's manual "
            "route"
        )
    pack_state, pack_bytes = detect_pack(out)
    if pack_state != PACK_BUILT:
        warnings.append(
            f"premium pack state: {pack_state} (the owner's local "
            "build-pack has not produced ciphertext for this bundle)"
        )
    public_key = None
    shared = out / "shared.js"
    if shared.is_file():
        public_key = public_key_hex_from_shared_js(
            shared.read_text(encoding="utf-8", errors="replace")
        )
    if not public_key:
        warnings.append(
            "no production license public key found in shared.js — "
            "license verification will refuse (by design)"
        )
    return {
        "generated_at": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "source": "repository site tree at bundle time",
        "pages": pages,
        "pack": {"state": pack_state, "bytes": pack_bytes},
        "modules": collect_modules(out),
        "public_key_hex": public_key,
        "rewired_constants": rewired,
        "brand_theme": brand or {},
        "buy_links_rewritten": buy_links or [],
        "files": copied,
        "warnings": warnings,
    }


def default_out() -> Path:
    """Where the webroot goes when --out isn't given:
    ``app/build/webroot`` — the folder site_bundle.webroot()
    finds in a checkout and the PyInstaller spec packages."""
    return Path(__file__).resolve().parent.parent / "build" / "webroot"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve()
    parser.add_argument(
        "--repo", type=Path, default=here.parent.parent.parent,
        help="repository root (the website tree)",
    )
    parser.add_argument(
        "--out", type=Path, default=default_out(),
        help="webroot output folder",
    )
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    copied = copy_site(repo, out)
    rewired = rewire_constants(out)
    buy_links = rewrite_buy_links(out)
    brand = apply_brand_theme(out)
    manifest = build_manifest(repo, out, copied, rewired, brand, buy_links)
    (out / "app-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Bundled {len(copied)} site files -> {out}")
    print(f"Pages: {manifest['pages']}")
    print(f"Pack: {manifest['pack']}")
    print(f"Rewired constants: {rewired}")
    print(f"Buy links pointed at the app: {buy_links}")
    print(f"Brand palette applied: {brand}")
    for warning in manifest["warnings"]:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
