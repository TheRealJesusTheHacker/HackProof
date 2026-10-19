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


def test_status_text_honest_about_unbuilt_pack(qapp, store, tmp_path,
                                               monkeypatch):
    """With a license but no built pack, the status must NOT
    claim the lessons are unlocked — the exam is, the lessons
    aren't in this edition yet, and the note says so."""
    from hackproof_app.gui.premium_page import PremiumPage

    page = premium_page(qapp, store, tmp_path, monkeypatch=monkeypatch)
    store.settings.license_key = "SOME-KEY"
    page.refresh()
    text = page._status_label.text()
    assert "Premium is active" in text
    assert "premium lessons and the final exam are unlocked" not in text
    assert "The final exam is unlocked." in text
    assert "still being prepared" in text
    # With the pack present, the full claim is the honest one.
    root = make_webroot(tmp_path / "webroot2")
    data = json.loads((root / "app-manifest.json").read_text())
    data["pack"] = {"state": "built", "bytes": 123}
    (root / "app-manifest.json").write_text(json.dumps(data))
    page2 = PremiumPage(store, make_manifest(root), verify_fn=verify_ok)
    _KEEP.append(page2)
    page2.refresh()
    assert "premium lessons and the final exam are unlocked" in (
        page2._status_label.text())


def test_qr_holder_reserves_its_space(qapp, store, tmp_path, monkeypatch):
    """The QR holder must be fixed-height and revealed with the
    order, so the payment status line can never slide under the
    native QR widget."""
    from PySide6.QtCore import Signal
    from PySide6.QtWidgets import QWidget

    from hackproof_app.gui.premium_page import PremiumPage

    class FakeQrView(QWidget):
        loadFinished = Signal(bool)

        def setUrl(self, _url):
            pass

    store.settings.service_base_url = "https://svc.example"
    root = make_webroot(tmp_path / "webroot")
    page = PremiumPage(
        store, make_manifest(root),
        client_factory=lambda base: StubClient(),
        verify_fn=verify_ok,
        qr_view_factory=FakeQrView,
    )
    _KEEP.append(page)
    assert page._qr_holder_widget.height() == 240
    assert not page._qr_holder_widget.isVisible()
    page.resize(1000, 1100)
    page.show()
    page._email.setText("buyer@example.com")
    page.submit_email()
    assert pump_until(lambda: page._payment_panel.isVisible())
    assert page._qr_holder_widget.isVisible()

    def _qr_above_status() -> bool:
        holder_bottom = page._qr_holder_widget.mapTo(
            page, page._qr_holder_widget.rect().bottomLeft()).y()
        status_top = page._pay_status.mapTo(
            page, page._pay_status.rect().topLeft()).y()
        return status_top >= holder_bottom

    # Measure the SETTLED layout. Holder and status line are
    # siblings in one QVBoxLayout, which never overlaps them once
    # it settles — but revealing the holder triggers a relayout
    # whose final pass can land a beat after the widget becomes
    # visible (the Windows runners caught a 5px mid-relayout
    # snapshot after a single processEvents). If the product ever
    # truly overlapped, this pump times out and the test fails.
    assert pump_until(_qr_above_status)
    holder_bottom = page._qr_holder_widget.mapTo(
        page, page._qr_holder_widget.rect().bottomLeft()).y()
    status_top = page._pay_status.mapTo(
        page, page._pay_status.rect().topLeft()).y()
    assert status_top >= holder_bottom


def test_web_view_real_profile_path(qapp, store, tmp_path):
    """The REAL profile path — no factory seam. Guards the class
    of bug where the window's own profile construction calls an
    API the installed Qt doesn't have (profile.scripts(), not
    userScripts()): every other GUI test injects a factory, and
    the failure mode is silent — the designed fallback page — so
    without this test the whole course could be dead on arrival
    while the suite stays green. Runs in a subprocess: it mirrors
    the frozen exe's --self-check-qt, and this VM's Qt build is
    known-fragile about web-engine objects living beside the
    rest of the suite in one process."""
    import os
    import subprocess
    import sys

    root = make_webroot(tmp_path / "webroot")
    program = (
        "import os, sys\n"
        "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')\n"
        "from PySide6.QtWidgets import QApplication\n"
        "app = QApplication(['probe'])\n"
        "try:\n"
        "    from PySide6.QtWebEngineCore import QWebEngineProfile\n"
        "    from PySide6.QtWebEngineWidgets import QWebEngineView\n"
        "    QWebEngineView()\n"
        "except Exception as exc:\n"
        "    print('ENV-SKIP', exc); sys.exit(3)\n"
        "from hackproof_app import setup_engine, site_bundle\n"
        "from hackproof_app.config import SettingsStore\n"
        "from hackproof_app.gui.main_window import MainWindow\n"
        f"store = SettingsStore({str(store.dir)!r})\n"
        f"root = {str(root)!r}\n"
        "from pathlib import Path\n"
        "win = MainWindow(store=store,"
        " manifest=site_bundle.load_manifest(Path(root)),"
        " webroot_path=Path(root),"
        " setup_state=setup_engine.SetupState.PORTABLE)\n"
        "view = win.ensure_web_view('course')\n"
        "print('REAL-VIEW-OK' if view is not None else 'REAL-VIEW-NONE')\n"
    )
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "--disable-gpu --no-sandbox --disable-dev-shm-usage",
    )
    env["HACKPROOF_DATA_DIR"] = str(store.dir)
    app_dir = str(Path(__file__).resolve().parent.parent)
    env["PYTHONPATH"] = app_dir + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True, text=True, env=env, timeout=120,
    )
    if proc.returncode == 3:
        pytest.skip("web engine cannot start in this environment")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "REAL-VIEW-OK" in proc.stdout, proc.stdout + proc.stderr[-2000:]


def test_scheme_allows_fetch_api(qapp):
    """The app scheme must carry FetchApiAllowed: without it the
    browser rejects every fetch() to the scheme while page loads
    still succeed — silently killing in-app certificate
    delivery, the one fetch the pages make."""
    from hackproof_app.gui import webview

    webview.register_scheme()
    scheme = webview.QWebEngineUrlScheme.schemeByName(
        webview.APP_SCHEME.encode())
    flag = getattr(webview.QWebEngineUrlScheme.Flag,
                   "FetchApiAllowed", None)
    if flag is not None:
        assert scheme.flags() & flag


def test_native_pages_are_scroll_wrapped(qapp, store, tmp_path):
    """Native pages live in scroll areas — on a short window
    their content scrolls instead of being squeezed or cut off.
    Web sections are not wrapped (their view scrolls itself)."""
    from PySide6.QtWidgets import QScrollArea

    from hackproof_app.gui import main_window as main_window_mod

    win = window(qapp, store, tmp_path)
    for row, (key, _label) in enumerate(main_window_mod._SECTIONS):
        child = win._stack.widget(row)
        if key in main_window_mod._PAGE_FILES:
            assert not isinstance(child, QScrollArea)
        else:
            assert isinstance(child, QScrollArea)
            assert child.widget() is win._pages[key]
    retire(win)


def test_window_reseeds_views_on_license_change(qapp, store, tmp_path):
    """Buying or removing a key on My Premium must reach the web
    views that already exist — otherwise the course stays locked
    (or unlocked) until the app is restarted."""
    win = window(qapp, store, tmp_path)

    class FakeView:
        def __init__(self):
            self.seeded = []
            self.cleared = []

        def seed_license(self, key):
            self.seeded.append(key)

        def clear_seeded_license(self, key):
            self.cleared.append(key)

    fake = FakeView()
    win._views["course"] = fake
    premium = win._pages["premium"]
    store.settings.license_key = "KEY-1"
    premium.license_changed.emit()
    assert fake.seeded == ["KEY-1"]
    store.settings.license_key = ""
    premium.license_changed.emit()
    assert fake.cleared == ["KEY-1"]
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
    # The field's label hides with it — no orphan label on the card.
    assert page._email_label.isHidden()
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
