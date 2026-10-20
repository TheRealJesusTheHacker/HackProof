"""App configuration: where HackProof keeps its data, and the
settings a person can change (today: the service base URL).

Data locations mirror the kit's conventions:

- **Portable mode** — ``HACKPROOF_DATA_DIR`` is set: every piece of
  app data (settings, the saved license key, the web profile) lives
  in that folder, and the app NEVER self-installs. This is the
  IT-Toolkit/USB edition contract, same as Argus's portable mode.
- **Installed / normal mode** — per-user data under
  ``%LOCALAPPDATA%\\Sentinel Safeguard\\HackProof`` on Windows
  (``~/.local/share/HackProof`` elsewhere). Per-user, never
  ProgramData: HackProof has no service and no machine-wide state,
  so nothing it keeps needs administrator territory.

The service base URL is the ONE configuration shared across the
whole product. The website's pages carry it in their
``CERT_SERVICE_BASE_URL`` constant; the app reads it from the
``HACKPROOF_SERVICE_BASE_URL`` environment variable when present,
else from the saved setting. Inside the app the pages never see
this value directly — the bundler points the bundled copies of
the pages at the app's own proxy origin, and the proxy forwards
to the base URL configured here (see
:mod:`hackproof_app.proxy_logic`).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

#: The shared configuration name for the payments/certificate
#: service base URL (environment-variable form). The Settings
#: screen edits the same value in the settings file.
SERVICE_BASE_ENV = "HACKPROOF_SERVICE_BASE_URL"

#: Portable-mode data directory variable (Argus's ARGUS_DATA_DIR
#: pattern): when set, data lives there and the app never installs.
DATA_DIR_ENV = "HACKPROOF_DATA_DIR"

SETTINGS_NAME = "settings.json"

IS_WINDOWS = sys.platform == "win32"


def is_portable() -> bool:
    """Portable mode: data lives beside wherever the owner pointed
    ``HACKPROOF_DATA_DIR``; the app never self-installs."""
    return bool(os.environ.get(DATA_DIR_ENV))


def data_dir() -> Path:
    """The folder holding settings, the license vault, the web
    profile, and the setup result hand-off file."""
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override)
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "Sentinel Safeguard" / "HackProof"
    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "HackProof"


def write_text_atomic(path: Path, text: str) -> Path:
    """Write *text* to *path* atomically (temp file + replace), so
    a crash mid-write can never leave a torn settings file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


@dataclass
class OrderRef:
    """The one open order the app is watching, if any. Persisted
    so closing the app mid-payment doesn't lose the order — the
    order id is the claim credential for the paid key."""

    order_id: str = ""
    email: str = ""

    def to_json(self) -> dict:
        return {"order_id": self.order_id, "email": self.email}

    @classmethod
    def from_json(cls, raw) -> "OrderRef":
        if not isinstance(raw, dict):
            return cls()
        return cls(
            order_id=str(raw.get("order_id") or ""),
            email=str(raw.get("email") or ""),
        )


@dataclass
class Settings:
    """Everything the app persists between runs."""

    #: Base URL of the payments/certificate service, e.g.
    #: ``https://payments.example.com`` — empty means "not
    #: connected yet": buying and automatic certificate delivery
    #: show their designed not-connected states, and everything
    #: else (the course, the exam, the manual certificate route)
    #: keeps working.
    service_base_url: str = ""
    #: The owner's premium license key, once entered. Stored in
    #: the per-user data folder exactly like the website stores it
    #: in the browser (it is the customer's own credential on the
    #: customer's own machine — the account, per the product's
    #: design).
    license_key: str = ""
    #: Name for the certificate, remembered from the exam gate.
    student_name: str = ""
    #: The open payment order being watched, if any.
    order: OrderRef = field(default_factory=OrderRef)
    #: The first-run install banner was dismissed.
    install_banner_dismissed: bool = False
    #: Clock-guard high-water mark (ms): the highest device clock
    #: seen at a successful license verification. Mirrors the
    #: website's localStorage guard in shared.js.
    max_clock_ms: int = 0
    #: Promo-code throttle state (see hackproof_app.promo):
    #: consecutive failed code attempts and when the last one
    #: happened (ms). Persisted so closing the app doesn't reset
    #: the wait; a successful unlock clears both.
    promo_fail_count: int = 0
    promo_last_fail_ms: int = 0

    # ---------------------------------------------------------- io

    def to_json(self) -> dict:
        return {
            "service_base_url": self.service_base_url,
            "license_key": self.license_key,
            "student_name": self.student_name,
            "order": self.order.to_json(),
            "install_banner_dismissed": self.install_banner_dismissed,
            "max_clock_ms": self.max_clock_ms,
            "promo_fail_count": self.promo_fail_count,
            "promo_last_fail_ms": self.promo_last_fail_ms,
        }

    @classmethod
    def from_json(cls, raw) -> "Settings":
        if not isinstance(raw, dict):
            return cls()
        try:
            max_clock_ms = int(raw.get("max_clock_ms") or 0)
        except (TypeError, ValueError):
            max_clock_ms = 0  # a hand-edited file never wedges startup

        def _count(name: str) -> int:
            try:
                return max(0, int(raw.get(name) or 0))
            except (TypeError, ValueError):
                return 0

        return cls(
            service_base_url=str(raw.get("service_base_url") or ""),
            license_key=str(raw.get("license_key") or ""),
            student_name=str(raw.get("student_name") or ""),
            order=OrderRef.from_json(raw.get("order")),
            install_banner_dismissed=bool(
                raw.get("install_banner_dismissed")
            ),
            max_clock_ms=max_clock_ms,
            promo_fail_count=_count("promo_fail_count"),
            promo_last_fail_ms=_count("promo_last_fail_ms"),
        )

    # ------------------------------------------------------ access

    def effective_service_base_url(self) -> str:
        """The base URL the app actually uses: the environment
        wins over the saved setting (so support can point a build
        at a different service without touching the file), and
        trailing slashes are normalized away."""
        env = os.environ.get(SERVICE_BASE_ENV)
        base = env if env is not None else self.service_base_url
        return (base or "").strip().rstrip("/")


class SettingsStore:
    """Load/save :class:`Settings` in the app data folder."""

    def __init__(self, directory: Path | None = None):
        self.dir = Path(directory) if directory else data_dir()
        self.path = self.dir / SETTINGS_NAME
        self.settings = self._load()

    def _load(self) -> Settings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return Settings()
        return Settings.from_json(raw)

    def save(self) -> Path:
        return write_text_atomic(
            self.path,
            json.dumps(self.settings.to_json(), indent=2),
        )

    # The license clock-guard seam used by license_keys.verify_license:
    def clock_high_water_ms(self) -> int:
        return self.settings.max_clock_ms

    def record_clock_ms(self, ms: int) -> None:
        if ms > self.settings.max_clock_ms:
            self.settings.max_clock_ms = ms
            self.save()
