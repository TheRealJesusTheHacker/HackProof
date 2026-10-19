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
  as the encrypted pack, never as readable lessons). The game's
  pages are excluded (the game was removed from the product);
  its built pack artifact, when present, is still picked up.
- **Rewires the service constants** in the bundled copies only:
  the pages' ``CERT_SERVICE_BASE_URL`` (and any sibling
  ``*_BASE_URL`` / ``*_STATUS_ENDPOINT`` constant) is pointed at
  the app origin ``hackproof://app`` so in-app page requests land
  in the app's proxy, which forwards them to the service base URL
  from the app's Settings. Repository files are never touched.
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
    "game", "__pycache__", "node_modules",
}
EXCLUDED_SUFFIXES = {".py", ".pyc", ".pyo"}
PACK_MARKER = "/*__PREMIUM_PACK__*/"
CONST_PATTERN = re.compile(
    r"((?:const\s+)?[A-Z][A-Z0-9_]*(?:BASE_URL|STATUS_ENDPOINT)"
    r"\s*=\s*\")[^\"]*(\")"
)


def _iter_site_files(repo: Path):
    for path in sorted(repo.rglob("*")):
        rel = path.relative_to(repo)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.is_dir():
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        yield rel, path


def copy_site(repo: Path, out: Path) -> list[str]:
    copied: list[str] = []
    for rel, src in _iter_site_files(repo):
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        copied.append(str(rel))
    # The built pack artifact lives under game/ today (keygen's
    # build-pack writes game/premium-pack.b64); ship the ciphertext
    # even though the game's pages are excluded.
    pack_file = repo / "game" / "premium-pack.b64"
    if pack_file.is_file():
        shutil.copyfile(pack_file, out / "premium-pack.b64")
        copied.append("premium-pack.b64")
    return copied


def rewire_constants(out: Path) -> list[str]:
    """Point the bundled pages' service constants at the app
    origin. Returns the list of "file:CONST" rewired."""
    rewired: list[str] = []
    for path in sorted(out.rglob("*.html")) + sorted(out.rglob("*.js")):
        text = path.read_text(encoding="utf-8", errors="replace")

        def _sub(match: re.Match) -> str:
            name = re.search(r"([A-Z][A-Z0-9_]*)\s*=", match.group(0))
            rewired.append(
                f"{path.relative_to(out)}:"
                f"{name.group(1) if name else 'CONST'}"
            )
            return match.group(1) + APP_ORIGIN + match.group(2)

        new = CONST_PATTERN.sub(_sub, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
    return rewired


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
                    {"path": str(path.relative_to(out)), "kind": "markdown"}
                )
            elif path.suffix == ".html":
                modules.append(
                    {"path": str(path.relative_to(out)), "kind": "page"}
                )
    return modules


def build_manifest(repo: Path, out: Path, copied: list[str],
                   rewired: list[str]) -> dict:
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
    manifest = build_manifest(repo, out, copied, rewired)
    (out / "app-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Bundled {len(copied)} site files -> {out}")
    print(f"Pages: {manifest['pages']}")
    print(f"Pack: {manifest['pack']}")
    print(f"Rewired constants: {rewired}")
    for warning in manifest["warnings"]:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
