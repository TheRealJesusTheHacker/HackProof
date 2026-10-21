"""The main window: academy-emerald chrome around the course.

Left navigation, one stacked content area (the Argus layout
language): **Course** and **Final Exam** and **Verify** are the
bundled website's own pages in the embedded browser; **My
Premium** is native (buy + license, see premium_page); **Settings**
and **About** are native and small.

Design rules honored here:

- No dead buttons: a section whose page isn't in this edition's
  bundle is disabled in the nav with the reason in its tooltip;
  a missing bundle or a missing browser component produces a
  designed explanation page, never a blank widget or a crash.
- Install is an OFFER, never a gate (a course needs nothing
  privileged): the banner appears when HackProof isn't installed,
  and the course is fully usable either way.
- Leaving the Exam section hides its web view — which is exactly
  the visibility change the exam's integrity layer counts, the
  semantics it was built for (see webview.py).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__, setup_engine, site_bundle
from ..config import SettingsStore
from ..service_client import ServiceClient
from .premium_page import PremiumPage

_SECTIONS = (
    ("course", "Course"),
    ("premium", "My Premium"),
    ("exam", "Final Exam"),
    ("verify", "Verify a Certificate"),
    ("settings", "Settings"),
    ("about", "About"),
)

_PAGE_FILES = {
    "course": "index.html",
    "exam": "exam.html",
    "verify": "verify.html",
}

_SEED_SCRIPT_NAME = "hackproof-license-seed"


def _message_page(title: str, text: str) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(22, 20, 22, 20)
    heading = QLabel(title)
    heading.setObjectName("Headline")
    heading.setWordWrap(True)
    layout.addWidget(heading)
    body = QLabel(text)
    body.setObjectName("Subhead")
    body.setWordWrap(True)
    layout.addWidget(body)
    layout.addStretch(1)
    return page


class MainWindow(QMainWindow):
    def __init__(self, *, store: SettingsStore | None = None,
                 manifest: site_bundle.SiteManifest | None = None,
                 webroot_path: Path | None = None,
                 setup_state: setup_engine.SetupState | None = None,
                 client_factory=None, verify_fn=None,
                 profile_factory=None, parent=None):
        super().__init__(parent)
        self._store = store or SettingsStore()
        self._root = webroot_path or site_bundle.webroot()
        self._manifest = manifest or site_bundle.load_manifest(self._root)
        self._setup_state = setup_state
        self._profile_factory = profile_factory
        self._profile = None
        self._seeded_key = self._store.settings.license_key
        self._views: dict[str, object] = {}
        self._result_timer: QTimer | None = None

        self.setWindowTitle("HackProof — Sentinel Safeguard")
        self.resize(1180, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setObjectName("Nav")
        self._nav.setFixedWidth(208)
        for key, label in _SECTIONS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._nav.addItem(item)
        outer.addWidget(self._nav)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self._banner = self._build_banner()
        right.addWidget(self._banner)
        self._stack = QStackedWidget()
        right.addWidget(self._stack, 1)
        outer.addLayout(right, 1)

        self._pages: dict[str, QWidget] = {}
        for key, _label in _SECTIONS:
            page = self._build_page(key, client_factory, verify_fn)
            self._pages[key] = page
            if key in _PAGE_FILES:
                # Web sections scroll inside their own view.
                self._stack.addWidget(page)
            else:
                # Native pages scroll as a whole: on a short
                # window nothing is ever squeezed or unreachable.
                self._stack.addWidget(self._scroll_wrapped(page))
        self._gate_nav_items()
        self._nav.currentRowChanged.connect(self._on_nav)
        self._nav.setCurrentRow(0)
        self._on_nav(0)
        self._refresh_banner()

    # ------------------------------------------------------------ pages

    @staticmethod
    def _scroll_wrapped(page: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setObjectName("PageScroll")
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        area.setWidget(page)
        return area

    def _build_page(self, key, client_factory, verify_fn) -> QWidget:
        if key == "premium":
            page = PremiumPage(
                self._store, self._manifest,
                client_factory=client_factory, verify_fn=verify_fn,
                qr_view_factory=self._make_qr_view,
            )
            page.license_changed.connect(self._reseed_views)
            return page
        if key == "settings":
            return self._build_settings_page()
        if key == "about":
            return self._build_about_page()
        # Web sections start as containers; the view is created on
        # first visit (lazy — startup never pays the browser's cost,
        # and a machine without the browser component still gets
        # every native screen).
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        return container

    def _gate_nav_items(self) -> None:
        """Disable nav entries whose page this bundle doesn't
        carry, with the reason — no dead buttons, ever."""
        reasons = {
            "exam": "The final exam isn't part of this edition's bundle.",
            "verify": "Certificate verification isn't part of this "
                      "edition's bundle.",
            "course": "The course files aren't part of this copy "
                      "of HackProof.",
        }
        for row in range(self._nav.count()):
            item = self._nav.item(row)
            key = item.data(Qt.ItemDataRole.UserRole)
            if key in _PAGE_FILES:
                present = (
                    self._root is not None
                    and self._manifest.page_present(key)
                )
                if not present:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                    item.setToolTip(reasons.get(key, ""))

    def _on_nav(self, row: int) -> None:
        if row < 0:
            return
        self._stack.setCurrentIndex(row)
        key = self._nav.item(row).data(Qt.ItemDataRole.UserRole)
        if key in _PAGE_FILES:
            self.ensure_web_view(key)

    # --------------------------------------------------------- web views

    def _ensure_profile(self):
        if self._profile is not None:
            return self._profile
        if self._profile_factory is not None:
            # Test seam: profile construction without the engine.
            self._profile = self._profile_factory(self)
            return self._profile
        from PySide6.QtWebEngineCore import QWebEngineProfile

        from ..config import data_dir
        from . import webview

        webview.register_scheme()
        profile = QWebEngineProfile("hackproof", self)
        storage = data_dir() / "webprofile"
        profile.setPersistentStoragePath(str(storage))
        profile.setCachePath(str(storage / "cache"))
        handler = webview.SiteSchemeHandler(
            self._root or Path("."),
            base_url_provider=lambda: (
                self._store.settings.effective_service_base_url()
            ),
            license_provider=lambda: self._store.settings.license_key,
            parent=self,
        )
        profile.installUrlSchemeHandler(
            webview.APP_SCHEME.encode(), handler
        )
        profile.scripts().insert(webview.bridge_script())
        self._profile = profile
        self._handler = handler
        self._sync_seed_script()
        return profile

    def _sync_seed_script(self) -> None:
        """Keep a document-creation seed script on the profile in
        step with the vault key. The pages read their saved key
        the moment they load — seeding on loadFinished is too
        late for a first open (the exam gate would ask for a key
        the app already holds). A script at document creation
        runs before any page script, so the very first open of
        every section already knows the key. Mirrors the
        seed_license semantics: never overwrites a key typed
        into a page, and removal clears only the copy the app
        itself seeded."""
        profile = self._profile
        if profile is None:
            return
        scripts_fn = getattr(profile, "scripts", None)
        if scripts_fn is None:
            return
        try:
            import json

            from PySide6.QtWebEngineCore import QWebEngineScript

            from .webview import LICENSE_STORAGE_KEY
        except Exception:
            return
        current = self._store.settings.license_key
        if current:
            source = (
                "try { if (!localStorage.getItem("
                f"{json.dumps(LICENSE_STORAGE_KEY)})) "
                "localStorage.setItem("
                f"{json.dumps(LICENSE_STORAGE_KEY)}, "
                f"{json.dumps(current)}); }} catch (e) {{}}"
            )
        elif self._seeded_key:
            source = (
                "try { if (localStorage.getItem("
                f"{json.dumps(LICENSE_STORAGE_KEY)}) === "
                f"{json.dumps(self._seeded_key)}) "
                "localStorage.removeItem("
                f"{json.dumps(LICENSE_STORAGE_KEY)}); }}"
                " catch (e) {}"
            )
        else:
            source = ""
        try:
            collection = scripts_fn()
            for old in collection.find(_SEED_SCRIPT_NAME):
                collection.remove(old)
            if source:
                script = QWebEngineScript()
                script.setName(_SEED_SCRIPT_NAME)
                script.setSourceCode(source)
                script.setInjectionPoint(
                    QWebEngineScript.InjectionPoint.DocumentCreation
                )
                script.setWorldId(
                    QWebEngineScript.ScriptWorldId.MainWorld
                )
                script.setRunsOnSubFrames(False)
                collection.insert(script)
        except Exception:
            pass  # loadFinished seeding remains as the fallback

    def _make_qr_view(self):
        try:
            profile = self._ensure_profile()
            from .webview import HackProofWebView

            return HackProofWebView(profile)
        except Exception:
            return None

    def ensure_web_view(self, key: str):
        """Create (once) and load the web view for a section.
        Returns the view, or None with a designed explanation in
        the section when the browser component is unavailable."""
        if key in self._views:
            return self._views[key]
        container = self._pages[key]
        layout = container.layout()
        if self._root is None:
            layout.addWidget(_message_page(
                "The course isn't in this copy",
                "This copy of HackProof was built without the course "
                "files, so there's nothing to open here yet. The "
                "official downloads from Sentinel Safeguard always "
                "include the full course.",
            ))
            self._views[key] = None
            return None
        try:
            profile = self._ensure_profile()
            from .webview import HackProofWebView

            view = HackProofWebView(profile, container)
        except Exception:
            layout.addWidget(_message_page(
                "The course browser couldn't start",
                "HackProof's built-in course browser isn't available "
                "on this PC right now, so course pages can't open. "
                "Your premium, settings, and this app's other "
                "sections still work. Reinstalling HackProof "
                "usually restores the browser.",
            ))
            self._views[key] = None
            return None
        layout.addWidget(view)
        view.loadFinished.connect(
            lambda _ok, v=view: v.seed_license(
                self._store.settings.license_key
            )
        )
        if self._store.settings.license_key:
            self._seeded_key = self._store.settings.license_key
        view.setUrl(QUrl(f"hackproof://app/{_PAGE_FILES[key]}"))
        self._views[key] = view
        return view

    def _reseed_views(self) -> None:
        """Keep the web sections in step with the vault: a key
        saved (or removed) on My Premium applies to the course,
        exam, and verify views that already exist — without this,
        a customer who buys in the app would find the course
        still locked until they restarted it."""
        current = self._store.settings.license_key
        for view in self._views.values():
            if view is None:
                continue
            if current:
                view.seed_license(current)
            elif self._seeded_key:
                view.clear_seeded_license(self._seeded_key)
        self._seeded_key = current
        self._sync_seed_script()

    # ------------------------------------------------------------ banner

    def _build_banner(self) -> QFrame:
        banner = QFrame()
        banner.setObjectName("Banner")
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(16, 10, 16, 10)
        self._banner_label = QLabel("")
        self._banner_label.setWordWrap(True)
        layout.addWidget(self._banner_label, 1)
        self._banner_install = QPushButton("Install HackProof")
        self._banner_install.setObjectName("Primary")
        self._banner_install.clicked.connect(self.begin_install)
        layout.addWidget(self._banner_install)
        dismiss = QPushButton("Not now")
        dismiss.clicked.connect(self._dismiss_banner)
        layout.addWidget(dismiss)
        return banner

    def _current_setup_state(self) -> setup_engine.SetupState:
        if self._setup_state is not None:
            return self._setup_state
        try:
            return setup_engine.detect_state()
        except Exception:
            return setup_engine.SetupState.NOT_INSTALLED

    def _refresh_banner(self) -> None:
        state = self._current_setup_state()
        dismissed = self._store.settings.install_banner_dismissed
        show = (
            state in (setup_engine.SetupState.NOT_INSTALLED,
                      setup_engine.SetupState.INSTALLED_INCOMPLETE)
            and not dismissed
        )
        self._banner.setVisible(show)
        if show:
            if state is setup_engine.SetupState.INSTALLED_INCOMPLETE:
                self._banner_label.setText(
                    "HackProof is partly set up on this PC. Finish "
                    "setup to add its Start Menu shortcut and Apps "
                    "& Features entry — the course works either way."
                )
                self._banner_install.setText("Finish setup")
            else:
                self._banner_label.setText(
                    "HackProof isn't installed on this PC yet. "
                    "Install it for a Start Menu shortcut and an "
                    "Apps & Features entry — the course works "
                    "either way."
                )
                self._banner_install.setText("Install HackProof")

    def _dismiss_banner(self) -> None:
        self._store.settings.install_banner_dismissed = True
        self._store.save()
        self._banner.setVisible(False)

    def begin_install(self) -> None:
        """Kick off setup: relaunch elevated and watch for the
        result file the helper leaves (Argus's hand-off)."""
        if setup_engine.is_elevated():
            from .setup_app import run_setup

            run_setup()
            self._setup_state = None
            self._refresh_banner()
            return
        if setup_engine.relaunch_as_admin(["--run-setup"]):
            self._banner_label.setText(
                "Setup is running in its own window — allow the "
                "Windows prompt, and this page will update when "
                "it's done."
            )
            self._watch_setup_result()
        else:
            self._banner_label.setText(
                "Windows didn't get the permission prompt. Choose "
                "Install to try again — HackProof needs that one "
                "prompt to place itself in Program Files."
            )

    def _watch_setup_result(self) -> None:
        if self._result_timer is not None:
            self._result_timer.stop()
        timer = QTimer(self)
        timer.setInterval(1500)
        state = {"ticks": 0}

        def check():
            state["ticks"] += 1
            result = setup_engine.read_setup_result()
            if result is not None:
                timer.stop()
                self._setup_state = None
                if result.get("ok"):
                    self._store.settings.install_banner_dismissed = False
                    self._banner_label.setText(
                        "All set — HackProof is installed. You'll "
                        "find it in your Start Menu."
                    )
                    self._banner_install.setVisible(False)
                    self._refresh_banner()
                else:
                    self._banner_label.setText(
                        str(result.get("message")
                            or "Setup didn't finish. Choose Install "
                               "to try again.")
                    )
            elif state["ticks"] > 80:  # ~2 minutes: stop watching
                timer.stop()

        timer.timeout.connect(check)
        timer.start()
        self._result_timer = timer

    def begin_uninstall(self) -> None:
        setup_engine.relaunch_as_admin(["--uninstall"])

    # ---------------------------------------------------------- settings

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        heading = QLabel("Settings")
        heading.setObjectName("Headline")
        layout.addWidget(heading)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_title = QLabel("Service connection")
        card_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        card_layout.addWidget(card_title)
        card_layout.addWidget(QLabel(
            "Where HackProof checks payments and sends "
            "certificates. Sentinel Safeguard sets this for "
            "official editions; it's here so your copy can be "
            "pointed at the service you're using."
        ))
        self._service_url = QLineEdit(
            self._store.settings.service_base_url
        )
        self._service_url.setPlaceholderText("https://…")
        card_layout.addWidget(self._service_url)
        row = QHBoxLayout()
        save = QPushButton("Save")
        save.setObjectName("Primary")
        save.clicked.connect(self._save_service_url)
        test = QPushButton("Test connection")
        test.clicked.connect(self._test_service_url)
        row.addWidget(save)
        row.addWidget(test)
        row.addStretch(1)
        card_layout.addLayout(row)
        self._service_status = QLabel("")
        self._service_status.setObjectName("Dim")
        self._service_status.setWordWrap(True)
        card_layout.addWidget(self._service_status)
        layout.addWidget(card)

        install_card = QFrame()
        install_card.setObjectName("Card")
        install_layout = QVBoxLayout(install_card)
        install_layout.setContentsMargins(18, 16, 18, 16)
        install_title = QLabel("HackProof on this PC")
        install_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        install_layout.addWidget(install_title)
        self._install_state_label = QLabel("")
        self._install_state_label.setWordWrap(True)
        install_layout.addWidget(self._install_state_label)
        row2 = QHBoxLayout()
        install_btn = QPushButton("Install / repair")
        install_btn.clicked.connect(self.begin_install)
        uninstall_btn = QPushButton("Uninstall HackProof")
        uninstall_btn.setObjectName("Danger")
        uninstall_btn.clicked.connect(self.begin_uninstall)
        row2.addWidget(install_btn)
        row2.addWidget(uninstall_btn)
        row2.addStretch(1)
        install_layout.addLayout(row2)
        layout.addWidget(install_card)
        self._refresh_install_label()
        layout.addStretch(1)
        return page

    def _refresh_install_label(self) -> None:
        state = self._current_setup_state()
        text = {
            setup_engine.SetupState.INSTALLED:
                "HackProof is installed on this PC.",
            setup_engine.SetupState.INSTALLED_INCOMPLETE:
                "HackProof is partly installed — repair finishes "
                "the job.",
            setup_engine.SetupState.NOT_INSTALLED:
                "HackProof isn't installed on this PC. The course "
                "works without installing; installing adds the "
                "Start Menu shortcut and the Apps & Features entry.",
            setup_engine.SetupState.PORTABLE:
                "This is the portable edition — it never installs; "
                "everything stays in its own folder.",
        }[state]
        self._install_state_label.setText(text)

    def _save_service_url(self) -> None:
        self._store.settings.service_base_url = (
            self._service_url.text().strip()
        )
        self._store.save()
        premium = self._pages.get("premium")
        if isinstance(premium, PremiumPage):
            premium.refresh()
        self._service_status.setText("Saved.")

    def _test_service_url(self) -> None:
        client = ServiceClient(self._service_url.text().strip())
        if not client.configured:
            self._service_status.setText(
                "No service address entered yet."
            )
            return
        self._service_status.setText("Checking…")
        from .premium_page import _Bridge, _run_async

        # The bridge must outlive the round trip — a queued signal
        # whose sender dies first is silently dropped.
        bridge = _Bridge()
        self._service_test_bridge = bridge

        def _done(r):
            self._service_test_bridge = None
            self._service_status.setText(
                "Connected — the service answered."
                if (r[0] and r[1])
                else "Couldn't reach that service. Check the "
                     "address and your connection."
            )

        bridge.done.connect(_done)
        _run_async(bridge, client.health)

    # -------------------------------------------------------------- about

    def _build_about_page(self) -> QWidget:
        pack_text = {
            site_bundle.PACK_BUILT:
                "The premium lesson pack is included in this edition.",
            site_bundle.PACK_NOT_BUILT:
                "This edition's premium lesson pack is still being "
                "prepared by Sentinel Safeguard — premium keys and "
                "purchases stay valid, and the lessons unlock as "
                "soon as an edition carrying the pack reaches you.",
            site_bundle.PACK_ABSENT:
                "This edition doesn't carry a premium lesson pack.",
        }[self._manifest.pack_state]
        text = (
            f"Version {__version__} · Published by Sentinel "
            "Safeguard LLC.\n\n"
            "HackProof is the Sentinel Safeguard cybersecurity "
            "course: learn how scams and attacks work so you can "
            "spot them, stop them, and recover — with a "
            "certificate at the end for those who pass the final "
            "exam.\n\n"
            f"{pack_text}\n\n"
            "Updates: this edition doesn't update itself. New "
            "editions are delivered as new downloads from Sentinel "
            "Safeguard — your license key and progress carry over."
        )
        return _message_page("About HackProof", text)
