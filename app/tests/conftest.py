"""App test suite setup.

Puts ``app/`` on sys.path (the package root) and provides the
shared fixtures: a headless QApplication for the GUI tests and an
isolated settings store in a temp folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    """One headless QApplication for the whole GUI suite."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def store(tmp_path):
    """A SettingsStore rooted in a temp data folder."""
    from hackproof_app.config import SettingsStore

    return SettingsStore(tmp_path / "data")


def pump_until(predicate, timeout_s: float = 5.0) -> bool:
    """Spin the Qt event loop until *predicate* holds (worker
    threads deliver their results through queued signals)."""
    import time

    from PySide6.QtCore import QCoreApplication

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()
