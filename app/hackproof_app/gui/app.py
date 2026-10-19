"""The GUI bootstrap: the one place a plain launch becomes an app.

Order matters here (the Argus lesson): the URL scheme must be
registered before any web-engine profile exists, the theme goes
on before any window is built, and a failure to start the browser
component must degrade into designed pages — never take the whole
app down (MainWindow handles that per-section).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .. import DISPLAY_NAME
from ..config import SettingsStore, data_dir
from ..site_bundle import load_manifest, webroot

log = logging.getLogger("hackproof")


def _setup_logging() -> None:
    """Best-effort file log in the data folder. Logging must
    never be the reason the app doesn't open."""
    try:
        folder = data_dir()
        folder.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=str(folder / "hackproof.log"),
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )
    except Exception:
        logging.basicConfig(level=logging.CRITICAL)


def _app_icon():
    """The window icon from the packaged asset, when present."""
    from PySide6.QtGui import QIcon

    icon_path = Path(__file__).resolve().parent / "assets" / "hackproof.png"
    if icon_path.is_file():
        return QIcon(str(icon_path))
    return None


def run_gui(argv: list[str] | None = None) -> int:
    """Open the HackProof main window. Returns the exit code."""
    _setup_logging()
    from PySide6.QtWidgets import QApplication

    from . import theme, webview
    from .main_window import MainWindow

    # The scheme must exist before the first profile is created.
    try:
        webview.register_scheme()
    except Exception:
        log.exception("could not register the app URL scheme")

    app = QApplication.instance() or QApplication(
        [sys.argv[0] or "HackProof.exe"]
    )
    app.setApplicationName("HackProof")
    app.setOrganizationName("Sentinel Safeguard LLC")
    app.setApplicationDisplayName(DISPLAY_NAME)
    theme.apply_theme(app)
    icon = _app_icon()
    if icon is not None:
        app.setWindowIcon(icon)

    store = SettingsStore()
    manifest = load_manifest(webroot())
    window = MainWindow(store=store, manifest=manifest)
    if icon is not None:
        window.setWindowIcon(icon)
    window.show()
    log.info("HackProof GUI started (bundle: %s)", webroot())
    return app.exec()
