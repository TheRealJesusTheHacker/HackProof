"""The embedded browser: serves the bundled course and enforces
the product's rules around it.

Four jobs:

1. **Serve the bundle.** Pages load from ``hackproof://app/...``
   through :class:`SiteSchemeHandler`, which reads files from the
   bundled webroot (:mod:`hackproof_app.site_bundle`). The scheme
   is registered as a secure, local scheme — that matters: the
   exam's certificate proof needs WebCrypto (``crypto.subtle``),
   which browsers only expose in secure contexts.

2. **Proxy the service calls.** The pages are rewired at bundle
   time to call ``hackproof://app/api/...``; the handler forwards
   those to the real service base URL from Settings and shapes
   the traffic with :mod:`hackproof_app.proxy_logic` (including
   the documented certificate-contract compatibility shim that
   supplies the student's license key from the app vault and the
   integrity block in the position the service reads). Replies
   always carry the service's JSON body; the pages drive their
   states off the body's ``status`` field, which the proxy keeps
   truthful.

3. **Reinforce copy protection.** The course is a paid product
   with copy protection on the pages themselves; the app frame
   adds the native half: the Copy/Cut/View-source/Inspect page
   actions are disabled and the context menu offers navigation
   and Paste only — **Paste stays available everywhere**, because
   pasting a license key or a certificate code is a designed
   flow, never something to block.

4. **Confine navigation.** The views share one persistent
   profile, and the scheme handler answers any request to the
   app origin — including proxying service calls and injecting
   the vault license into certificate submissions. So a page
   must never be able to steer the view somewhere else:
   :class:`HackProofWebPage` classifies every navigation with
   :func:`hackproof_app.proxy_logic.navigation_decision` —
   app-origin targets navigate in-app (every course page, the
   buy guidance page, and the reader/QR assets live there),
   web links open in the system browser, and anything else is
   refused.

Exam integrity note: the exam page counts tab switches through
``visibilitychange`` and window blurs. The app's navigation is a
stacked widget — switching sections hides the exam view, which is
exactly the visibility change the page is listening for, and the
window losing focus blurs it natively. No site code was changed
for this; the semantics the integrity layer was built for are
the semantics the shell naturally produces.
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineUrlRequestJob,
    QWebEngineUrlScheme,
    QWebEngineUrlSchemeHandler,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMenu

from .. import __version__, proxy_logic, site_bundle
from ..proxy_logic import APP_HOST, APP_SCHEME

_ASSETS = Path(__file__).resolve().parent / "assets"

#: localStorage key the website uses for the license
#: (shared.js CONFIG.LICENSE_STORAGE_KEY) — the app seeds it from
#: its vault so a key entered once natively unlocks the pages too.
LICENSE_STORAGE_KEY = "hackproof_license_v1"

_MIME_OVERRIDES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


_SCHEME_REGISTERED = False


def register_scheme() -> None:
    """Register the ``hackproof`` scheme. Must run before any
    QWebEngineProfile is created. Idempotent: the bootstrap and
    the profile factory both call it, and Qt keeps the first
    registration — later calls here are no-ops by design."""
    global _SCHEME_REGISTERED
    if _SCHEME_REGISTERED:
        return
    scheme = QWebEngineUrlScheme(APP_SCHEME.encode())
    flags = (
        QWebEngineUrlScheme.Flag.SecureScheme
        | QWebEngineUrlScheme.Flag.LocalScheme
        | QWebEngineUrlScheme.Flag.LocalAccessAllowed
    )
    # CorsEnabled exists on newer Qt; same-origin traffic doesn't
    # need it, so its absence is not an error.
    cors = getattr(QWebEngineUrlScheme.Flag, "CorsEnabled", None)
    if cors is not None:
        flags |= cors
    # FetchApiAllowed is the load-bearing one: without it the
    # browser rejects every fetch() to this scheme ("Failed to
    # fetch") while page loads still work — which silently kills
    # in-app certificate delivery, the one fetch the pages make.
    fetch_api = getattr(QWebEngineUrlScheme.Flag, "FetchApiAllowed", None)
    if fetch_api is not None:
        flags |= fetch_api
    scheme.setFlags(flags)
    QWebEngineUrlScheme.registerScheme(scheme)
    _SCHEME_REGISTERED = True


def bridge_script() -> QWebEngineScript:
    """The document-creation script identifying the app shell to
    the pages (and freezing the identity so page code can rely
    on it). Carries no secrets and grants no capabilities."""
    script = QWebEngineScript()
    script.setName("hackproof-app-bridge")
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(False)
    script.setSourceCode(
        "window.__HACKPROOF_APP__ = Object.freeze({"
        'name: "HackProof", shell: "windows-app", '
        f"version: {json.dumps(__version__)}"
        "});"
    )
    return script


class SiteSchemeHandler(QWebEngineUrlSchemeHandler):
    """Serves the bundled site and proxies /api to the service.

    *base_url_provider* and *license_provider* are callables so the
    handler always sees the CURRENT settings/vault, not a snapshot
    taken at startup.
    """

    def __init__(self, root: Path, base_url_provider, license_provider,
                 parent=None):
        super().__init__(parent)
        self._root = Path(root)
        self._base_url = base_url_provider
        self._license = license_provider
        self._net = QNetworkAccessManager(self)
        self._pending: dict[int, tuple] = {}
        self._pending_bodies: dict[int, tuple] = {}

    # ---------------------------------------------------------- dispatch

    def requestStarted(self, job: QWebEngineUrlRequestJob) -> None:  # noqa: N802
        url = job.requestUrl()
        path = url.path() or "/"
        if proxy_logic.is_api_path(path):
            self._proxy(job, path, url.query())
            return
        if path.startswith("/_app/"):
            self._serve_asset(job, path[len("/_app/"):])
            return
        self._serve_site(job, path, url)

    # ------------------------------------------------------ site files

    def _serve_site(self, job, path: str, url: QUrl) -> None:
        rel = path.lstrip("/")
        if rel == "" or rel.endswith("/"):
            rel += "index.html"
        target = (self._root / rel).resolve()
        root = self._root.resolve()
        if root not in target.parents and target != root:
            self._serve_not_found(job)  # traversal attempt: no leak
            return
        if target.is_dir():
            target = target / "index.html"
        if url.query() == "raw=1" and target.suffix == ".md":
            self._reply_file(job, target)
            return
        if target.suffix == ".md" and target.is_file():
            # Markdown lessons open in the app's reader template,
            # which fetches the raw file itself (?raw=1 above).
            self._serve_asset(job, "mdview.html")
            return
        if not target.is_file():
            self._serve_not_found(job)
            return
        self._reply_file(job, target)

    def _serve_asset(self, job, name: str) -> None:
        name = Path(name).name  # assets are flat; no traversal
        target = _ASSETS / name
        if not target.is_file():
            self._serve_not_found(job)
            return
        self._reply_file(job, target)

    def _serve_not_found(self, job) -> None:
        page = _ASSETS / "notfound.html"
        try:
            body = page.read_bytes()
        except OSError:
            body = b"<h1>Not found</h1>"
        self._reply_bytes(job, body, "text/html; charset=utf-8")

    def _reply_file(self, job, target: Path) -> None:
        try:
            body = target.read_bytes()
        except OSError:
            self._serve_not_found(job)
            return
        mime = _MIME_OVERRIDES.get(
            target.suffix.lower(),
            mimetypes.guess_type(target.name)[0] or "application/octet-stream",
        )
        self._reply_bytes(job, body, mime)

    def _reply_bytes(self, job, body: bytes, mime: str) -> None:
        buffer = QBuffer(self)
        buffer.setData(QByteArray(body))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        key = id(job)
        self._pending[key] = (job, buffer)
        job.destroyed.connect(lambda *_: self._pending.pop(key, None))
        job.reply(mime.encode(), buffer)

    # ------------------------------------------------------------ proxy

    def _proxy(self, job, path: str, query: str) -> None:
        base = self._base_url()
        target = proxy_logic.proxy_target(base, path, query)
        if target is None:
            self._reply_bytes(
                job,
                json.dumps(proxy_logic.NOT_CONFIGURED_BODY).encode(),
                "application/json",
            )
            return
        method = bytes(job.requestMethod()).decode("ascii", "replace")
        if method in ("POST", "PUT"):
            # The request body device is sequential and arrives
            # asynchronously — it must be opened and drained via
            # its signals. Reading it synchronously here returns
            # zero bytes (proven in the polish audit: every
            # in-app certificate submission arrived empty).
            self._read_body_async(
                job,
                lambda body: self._proxy_send(
                    job, path, target, method, body
                ),
            )
        else:
            self._proxy_send(job, path, target, method, b"")

    def _proxy_send(self, job, path, target, method, body) -> None:
        if path == "/api/certificates" and method == "POST" and body:
            try:
                parsed = json.loads(body.decode("utf-8"))
                parsed = proxy_logic.normalize_cert_request(
                    parsed, self._license()
                )
                body = json.dumps(parsed).encode("utf-8")
            except (ValueError, UnicodeDecodeError):
                pass  # forward the original bytes; the service judges
        request = QNetworkRequest(QUrl(target))
        request.setHeader(
            QNetworkRequest.KnownHeaders.ContentTypeHeader,
            "application/json",
        )
        request.setRawHeader(b"Accept", b"application/json")
        if method == "POST":
            reply = self._net.post(request, QByteArray(body or b""))
        elif method == "PUT":
            reply = self._net.put(request, QByteArray(body or b""))
        elif method == "DELETE":
            reply = self._net.deleteResource(request)
        else:
            reply = self._net.get(request)
        reply.finished.connect(
            lambda: self._proxy_finished(job, reply, path)
        )

    def _read_body_async(self, job, callback) -> None:
        """Collect a request body from its sequential device and
        call *callback* with the complete bytes. The device is
        not open at requestStarted and reports size 0 — it has
        to be opened, then drained. Draining is POLLED on a
        timer, never signal-driven: the body device is an
        internal QIODevice subclass, and connecting to its
        signals from Python segfaults (proven in the polish
        audit — faulthandler pinned the crash to the connect
        call). Polling readAll()/atEnd() touches only plain
        methods and is safe."""
        device = job.requestBody()
        if device is None:
            callback(b"")
            return
        try:
            if not device.isOpen() and not device.open(
                QIODevice.OpenModeFlag.ReadOnly
            ):
                callback(b"")
                return
        except Exception:
            callback(b"")
            return
        chunks = bytearray()
        state = {"done": False, "dead": False, "ticks": 0}
        key = id(job)
        timer = QTimer(self)
        timer.setInterval(10)
        self._pending_bodies[key] = (job, device, timer)

        def finish():
            if state["done"] or state["dead"]:
                return
            state["done"] = True
            timer.stop()
            chunks.extend(bytes(device.readAll()))
            self._pending_bodies.pop(key, None)
            callback(bytes(chunks))

        def tick():
            if state["done"] or state["dead"]:
                timer.stop()
                return
            state["ticks"] += 1
            data = bytes(device.readAll())
            if data:
                chunks.extend(data)
            # atEnd: the upload channel has closed and the
            # buffer is drained. The tick cap (~10 s) is a safety
            # net — forward what arrived rather than hang.
            if device.atEnd() or state["ticks"] > 1000:
                finish()

        def mark_dead(*_):
            state["dead"] = True
            timer.stop()
            self._pending_bodies.pop(key, None)

        job.destroyed.connect(mark_dead)
        timer.timeout.connect(tick)
        timer.start()
        tick()

    def _proxy_finished(self, job, reply: QNetworkReply, path: str) -> None:
        try:
            raw = bytes(reply.readAll())
            if reply.error() != QNetworkReply.NetworkError.NoError and not raw:
                raw = json.dumps(
                    {"error": "the service could not be reached"}
                ).encode()
            if path == "/api/certificates" and raw:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                    raw = json.dumps(
                        proxy_logic.normalize_cert_response(parsed)
                    ).encode("utf-8")
                except (ValueError, UnicodeDecodeError):
                    pass
            self._reply_bytes(job, raw, "application/json")
        finally:
            reply.deleteLater()


def _open_external(url: QUrl) -> None:
    """Hand a web link to the system browser. A module-level
    seam so tests can observe the hand-off without opening a
    real browser."""
    QDesktopServices.openUrl(url)


class HackProofWebPage(QWebEnginePage):
    """A page that cannot wander off the app origin.

    Every navigation — link click, script-driven location
    change, redirect — is classified by
    :func:`hackproof_app.proxy_logic.navigation_decision`:
    app-origin targets proceed; a web link in the main frame
    opens in the system browser and the in-app navigation is
    refused (a web link inside a sub-frame is just refused —
    an embedded frame must never pop a browser window); every
    other scheme is refused outright. Fetches and resource
    loads are not navigations and are untouched, so the pages'
    service calls work exactly as before.
    """

    def acceptNavigationRequest(self, url, navigation_type,  # noqa: N802
                                is_main_frame) -> bool:
        decision = proxy_logic.navigation_decision(
            url.scheme(), url.host()
        )
        if decision == "app":
            return True
        if decision == "external" and is_main_frame:
            _open_external(url)
        return False


class HackProofWebView(QWebEngineView):
    """A course web view with the product's frame rules applied:
    copy protection reinforced, Paste preserved, no dev tools,
    navigation confined to the app origin."""

    _DISABLED_ACTIONS = (
        "Copy", "Cut", "ViewSource", "InspectElement",
        "SavePage", "CopyImage", "CopyImageUrl", "CopyLinkToHighlight",
        "OpenLinkInNewWindow", "OpenLinkInNewTab", "DownloadLinkToDisk",
        "DownloadImageToDisk", "DownloadMediaToDisk",
    )

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        page = HackProofWebPage(profile, self)
        self.setPage(page)
        self._harden(page)

    def _harden(self, page: QWebEnginePage) -> None:
        web_action = QWebEnginePage.WebAction
        for name in self._DISABLED_ACTIONS:
            action = getattr(web_action, name, None)
            if action is not None:
                page.action(action).setEnabled(False)
        # The bridge identity script is inserted ONCE, at profile
        # level, by whoever builds the profile (MainWindow /
        # entry's Qt check) — inserting it per-view would stack
        # duplicate copies on the shared profile.

    # A context menu with navigation + Paste only. Paste is a
    # designed flow (license keys, certificate codes) and is
    # never blocked; Copy/Cut never appear.
    def contextMenuEvent(self, event) -> None:  # noqa: N802
        page = self.page()
        web_action = QWebEnginePage.WebAction
        menu = QMenu(self)
        for label, action_name in (
            ("Back", "Back"), ("Forward", "Forward"), ("Reload", "Reload"),
        ):
            action = getattr(web_action, action_name, None)
            if action is not None and page.action(action).isEnabled():
                entry = menu.addAction(label)
                entry.triggered.connect(
                    lambda _=False, a=action: page.triggerAction(a)
                )
        menu.addSeparator()
        paste = menu.addAction("Paste")
        paste.triggered.connect(
            lambda: page.triggerAction(web_action.Paste)
        )
        menu.exec(event.globalPos())
        event.accept()

    # -------------------------------------------------- license seeding

    def seed_license(self, license_key: str) -> None:
        """Offer the vault's key to the page's localStorage when
        the page has none saved — one entry, everywhere unlocked.
        A key the person typed into a page is never overwritten."""
        if not license_key:
            return
        js = (
            "try { if (!localStorage.getItem("
            f"{json.dumps(LICENSE_STORAGE_KEY)})) localStorage.setItem("
            f"{json.dumps(LICENSE_STORAGE_KEY)}, {json.dumps(license_key)});"
            " } catch (e) {}"
        )
        self.page().runJavaScript(js)

    def clear_seeded_license(self, license_key: str) -> None:
        """Remove the page's copy of the vault's key — the mirror
        of seed_license, for "Remove key from this app". Only the
        exact key the app seeded is removed; a key the person
        typed into the page themselves is theirs and stays."""
        if not license_key:
            return
        js = (
            "try { if (localStorage.getItem("
            f"{json.dumps(LICENSE_STORAGE_KEY)}) === "
            f"{json.dumps(license_key)}) localStorage.removeItem("
            f"{json.dumps(LICENSE_STORAGE_KEY)}); }} catch (e) {{}}"
        )
        self.page().runJavaScript(js)
