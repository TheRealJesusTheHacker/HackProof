"""The bundled website: what the build-time bundler produced and
how the app finds it at runtime.

``app/tools/bundle_site.py`` copies the website (the repository's
site tree) into ``app/build/webroot/`` at build time and writes
``app-manifest.json`` into it: which pages exist, the state of the
premium pack, the free-module list, and the license public key it
read from ``shared.js``. PyInstaller's spec ships that folder
inside the executable as ``hackproof_webroot``; at runtime it is
extracted with the rest of the one-file bundle.

This module is the only place that knows those locations, and it
degrades honestly: no bundle (a developer running from a bare
checkout) yields ``webroot() is None`` and the GUI shows its
designed "course files aren't in this copy" state instead of a
broken browser.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .license_keys import public_key_hex_from_shared_js

MANIFEST_NAME = "app-manifest.json"
BUNDLED_DIR_NAME = "hackproof_webroot"

#: Explicit webroot override (support/dev): wins over every
#: packaged location in candidate_webroots().
WEBROOT_ENV = "HACKPROOF_WEBROOT"

#: Premium-pack states the manifest can report.
PACK_BUILT = "built"          # ciphertext present — premium can unlock
PACK_NOT_BUILT = "not-built"  # placeholder marker found, still empty
PACK_ABSENT = "absent"        # no pack trace in the site tree at all


@dataclass
class SiteManifest:
    pages: dict = field(default_factory=dict)   # name -> bool present
    pack_state: str = PACK_ABSENT
    pack_bytes: int = 0
    modules: list = field(default_factory=list)  # [{path, kind}]
    public_key_hex: str | None = None
    rewired_constants: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    generated_at: str = ""
    source: str = ""

    @classmethod
    def from_json(cls, raw) -> "SiteManifest":
        if not isinstance(raw, dict):
            return cls()
        pack = raw.get("pack") or {}
        return cls(
            pages=dict(raw.get("pages") or {}),
            pack_state=str(pack.get("state") or PACK_ABSENT),
            pack_bytes=int(pack.get("bytes") or 0),
            modules=list(raw.get("modules") or []),
            public_key_hex=raw.get("public_key_hex") or None,
            rewired_constants=list(raw.get("rewired_constants") or []),
            warnings=list(raw.get("warnings") or []),
            generated_at=str(raw.get("generated_at") or ""),
            source=str(raw.get("source") or ""),
        )

    def page_present(self, name: str) -> bool:
        return bool(self.pages.get(name))


def candidate_webroots() -> list[Path]:
    """Where a webroot may live, in the order they win."""
    roots: list[Path] = []
    env = os.environ.get(WEBROOT_ENV)
    if env:
        roots.append(Path(env))
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:  # PyInstaller one-file extraction dir
        roots.append(Path(meipass) / BUNDLED_DIR_NAME)
    here = Path(__file__).resolve()
    # app/build/webroot relative to the package (dev / CI checkout)
    roots.append(here.parent.parent / "build" / "webroot")
    # beside a frozen executable (should the layout ever change)
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent / BUNDLED_DIR_NAME)
    return roots


def webroot() -> Path | None:
    """The bundled website folder, or None when this copy of the
    app carries none."""
    for root in candidate_webroots():
        if (root / MANIFEST_NAME).is_file() or (root / "index.html").is_file():
            return root
    return None


def load_manifest(root: Path | None = None) -> SiteManifest:
    """The bundle manifest; an empty one when the file is missing
    or unreadable (the GUI treats that as "no course bundle")."""
    root = root or webroot()
    if root is None:
        return SiteManifest()
    try:
        raw = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SiteManifest()
    manifest = SiteManifest.from_json(raw)
    if not manifest.public_key_hex:
        # The manifest is a build artifact; shared.js is the source
        # of truth. If one is missing the key, ask the other.
        try:
            manifest.public_key_hex = public_key_hex_from_shared_js(
                (root / "shared.js").read_text(encoding="utf-8")
            )
        except OSError:
            pass
    return manifest
