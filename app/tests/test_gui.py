"""GUI tests (headless, offscreen): theme discipline, main-window
construction and nav gating, the designed degradation when the
browser component is unavailable, the full Premium buy/key flows
against stub service + stub verifier, and the setup dialog's
close-hardening."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hackproof_app import license_keys, setup_engine, site_bundle
from hackproof_app.gui import theme
from hackproof_app.license_keys import LicenseError, LicenseInfo
from hackproof_app.service_client import Order
from conftest import pump_until

PUB = "ab" * 32


#: Widgets created by the GUI tests live here for the whole
#: session. This VM's Qt build segfaults when the garbage
#: collector tears down a whole window graph (proven by bisection:
#: Qt's own deferred destruction is clean, GC teardown is not) —
#: and a failing test's traceback would hold the frame, then drop
#: it mid-report with the same result. Production never hits this:
#: the window lives until the app exits through the event loop.
_KEEP: list = []


def retire(widget):
    """Close a widget and keep it referenced for the session
    (see _KEEP). The OS reclaims everything at process exit."""
    widget.close()
    _KEEP.append(widget)


def make_webroot(root: Path, *, exam: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text("<h1>Course</h1>")
    if exam:
        (root / "exam.html").write_text("<h1>Exam</h1>")
    (root / "verify.html").write_text("<h1>Verify</h1>")
    (root / "app-manifest.json").write_text(json.dumps({
        "pages": {"course": True, "exam": exam, "verify": True},
        "pack": {"state": "not-built", "bytes": 0},
        "modules": [], "public_key_hex": PUB, "warnings": [],
    }))
    return root


def make_manifest(root: Path) -> site_bundle.SiteManifest:
    return site_bundle.load_manifest(root)


# ------------------------------------------------------------- theme


def test_theme_is_green_black_no_purple(qapp):
    theme.apply_theme(qapp)
    palette = qapp.palette()
    from PySide6.QtGui import QPalette

    assert palette.color(QPalette.ColorRole.Window).name() == "#060a07"
    assert palette.color(QPalette.ColorRole.WindowText).name() == "#e8f2ea"
    qss = qapp.styleSheet().lower()
    for purple in ("#a855f7", "#7c3aed", "#8b5cf6", "purple", "#9333ea"):
        assert purple not in qss
    assert "#2ee06f" in qss  # Sentinel green is the accent


# -------------------------------------------------------- main window


def _no_engine_profile(parent):
    # Deterministic "browser component unavailable" for the suite:
    # the real import is exercised by the Windows CI self-check.
    raise ImportError("QtWebEngine unavailable in this environment")


def window(qapp, store, tmp_path, *, exam=True,
           state=setup_engine.SetupState.PORTABLE):
    from hackproof_app.gui.main_window import MainWindow

    root = make_webroot(tmp_path / "webroot", exam=exam)
    win = MainWindow(
        store=store, manifest=make_manifest(root), webroot_path=root,
        setup_state=state, profile_factory=_no_engine_profile,
    )
    _KEEP.append(win)
    return win


def test_main_window_constructs(qapp, store, tmp_path):
    win = window(qapp, store, tmp_path)
    assert win.windowTitle().startswith("HackProof")
    assert win._nav.count() == 6
    retire(win)


def test_nav_gates_missing_exam(qapp, store, tmp_path):
    win = window(qapp, store, tmp_path, exam=False)
    from PySide6.QtCore import Qt

    exam_item = win._nav.item(2)
    assert exam_item.data(Qt.ItemDataRole.UserRole) == "exam"
    assert not exam_item.isSelected()
    assert not (exam_item.flags() & Qt.ItemFlag.ItemIsEnabled)
    assert "isn't part of this edition" in exam_item.toolTip()
    retire(win)


def test_web_view_degrades_designed_when_engine_missing(qapp, store, tmp_path):
    win = window(qapp, store, tmp_path)
    view = win.ensure_web_view("course")
    if view is None:
        # The designed fallback: an explanation, not a blank page.
        container = win._pages["course"]
        from PySide6.QtWidgets import QLabel

        texts = [lb.text() for lb in container.findChildren(QLabel)]
        assert any("course" in t.lower() for t in texts), texts
    else:  # a machine WITH the engine: the view points at the app origin
        assert view.url().scheme() == "hackproof"
    retire(win)


def test_install_banner_offer_states(qapp, store, tmp_path):
    win = window(qapp, store, tmp_path,
                 state=setup_engine.SetupState.NOT_INSTALLED)
    assert not win._banner.isHidden()
    assert "isn't installed" in win._banner_label.text()
    win2 = window(qapp, store, tmp_path / "b",
                  state=setup_engine.SetupState.INSTALLED)
    assert win2._banner.isHidden()
    retire(win)
    retire(win2)


def test_settings_save_service_url(qapp, store, tmp_path):
    win = window(qapp, store, tmp_path)
    win._service_url.setText("https://svc.example/")
    win._save_service_url()
    assert store.settings.service_base_url == "https://svc.example/"
    fresh = type(store)(store.dir)
    assert fresh.settings.service_base_url == "https://svc.example/"
    retire(win)


# ------------------------------------------------------- premium page


class StubClient:
    def __init__(self):
        self.order = Order(
            order_id="hp_1", status="awaiting_payment",
            btc_address="bc1qaddress", btc_amount_sats=6123,
            btc_amount_btc="0.00006123", price_usd=5.0,
            confirmations=0, expires_at="2030-01-01T00:00:00Z",
        )
        self.polled = None

    def create_order(self, email):
        self.created_for = email
        return self.order

    def get_order(self, order_id):
        return self.polled or self.order


def verify_ok(text, pub, *, now_ms=None, high_water_ms=None):
    if not text.strip():
        raise LicenseError("Paste your key first.")
    return LicenseInfo(
        id="t1", tier="premium", expiry=2_000_000_000, secret=b"s" * 32,
    )


def verify_bad(text, pub, *, now_ms=None, high_water_ms=None):
    raise LicenseError(
        "That key isn't genuine — check it for typos and try again."
    )


def premium_page(qapp, store, tmp_path, client=None, verify=verify_ok,
                 monkeypatch=None):
    if monkeypatch is not None:
        monkeypatch.delenv("HACKPROOF_SERVICE_BASE_URL", raising=False)
    from hackproof_app.gui.premium_page import PremiumPage

    root = make_webroot(tmp_path / "webroot")
    page = PremiumPage(
        store, make_manifest(root),
        client_factory=lambda base: client or StubClient(),
        verify_fn=verify,
    )
    _KEEP.append(page)
    return page


def test_premium_unconfigured_buy_state(qapp, store, tmp_path, monkeypatch):
    page = premium_page(qapp, store, tmp_path, monkeypatch=monkeypatch)
    assert "isn't switched on" in page._buy_note.text()
    assert page._email.isHidden()
    retire(page)


def test_premium_buy_flow_to_paid_key(qapp, store, tmp_path, monkeypatch):
    store.settings.service_base_url = "https://svc.example"
    client = StubClient()
    page = premium_page(qapp, store, tmp_path, client=client,
                        monkeypatch=monkeypatch)
    emitted = []
    page.license_changed.connect(lambda: emitted.append(True))
    page.show()  # isVisible() needs the whole chain visible
    page._email.setText("buyer@example.com")
    page.submit_email()
    assert pump_until(lambda: page._payment_panel.isVisible())
    assert "0.00006123" in page._pay_amount.text()
    assert page._pay_address.text() == "bc1qaddress"
    assert store.settings.order.order_id == "hp_1"

    client.polled = Order(
        order_id="hp_1", status="paid", btc_address="bc1qaddress",
        btc_amount_sats=6123, btc_amount_btc="0.00006123",
        price_usd=5.0, confirmations=1,
        expires_at="2030-01-01T00:00:00Z",
        license_key="MINTED-KEY", delivery="emailed",
    )
    page._poll_order_now()
    assert pump_until(lambda: page._save_arrived_btn.isVisible())
    assert "emailed" in page._pay_status.text()
    page._save_arrived_key()
    assert store.settings.license_key == "MINTED-KEY"
    assert emitted  # the window re-seeds course views on this signal
    assert "Premium is active" in page._status_label.text()
    retire(page)


def test_premium_key_unlock_and_refusal(qapp, store, tmp_path, monkeypatch):
    page = premium_page(qapp, store, tmp_path, verify=verify_bad,
                        monkeypatch=monkeypatch)
    page._key_edit.setPlainText("FORGED")
    page.submit_key()
    assert "isn't genuine" in page._key_status.text()
    assert store.settings.license_key == ""

    page2 = premium_page(qapp, store, tmp_path / "b", verify=verify_ok,
                         monkeypatch=monkeypatch)
    page2._key_edit.setPlainText("REAL-KEY")
    page2.submit_key()
    assert store.settings.license_key == "REAL-KEY"
    assert "Premium is active" in page2._status_label.text()
    retire(page)
    retire(page2)


# ------------------------------------------------------- setup dialog


def test_progress_dialog_close_hardened(qapp):
    from PySide6.QtGui import QCloseEvent

    from hackproof_app.gui.setup_app import STEP_LABELS, ProgressDialog

    # Every engine step has plain-language copy.
    for step in (setup_engine.STEP_PLACING, setup_engine.STEP_REGISTERING,
                 setup_engine.STEP_SHORTCUTS, setup_engine.STEP_VERIFYING):
        assert step in STEP_LABELS

    dialog = ProgressDialog("Setting up", "Setting up HackProof…")
    event = QCloseEvent()
    dialog.closeEvent(event)
    assert not event.isAccepted()  # ignored while work runs
    assert "Still working" in dialog.status_label.text()
    dialog.finish_ok("All done")
    event2 = QCloseEvent()
    dialog.closeEvent(event2)
    assert event2.isAccepted()
    dialog.finish_error("plain words")
    assert dialog.heading.text() == "Something needs your attention"
    retire(dialog)


def test_license_keys_module_imported_for_contract():
    # The page wiring uses the real verifier by default.
    assert license_keys.verify_license is not None
