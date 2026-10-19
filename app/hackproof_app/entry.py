"""The one entry point of the packaged HackProof.exe.

A single executable is the whole product; how it was launched
decides what it does (the ARGUS.EXE pattern):

- ``--run-setup`` → the elevated setup helper: run the self-install
  engine with a small progress window, leave a result file for the
  GUI, exit.
- ``--uninstall`` → the uninstaller flow (self-elevates, plain
  confirm dialog, progress, done).
- ``--self-check`` → the release pipeline's smoke test: import
  every lazily-loaded module the packaged build needs (the Qt
  stack, QtWebEngine above all), print the version, exit 0 without
  opening any window. A module that fails to import is named and
  the exit code is nonzero.
- ``--self-check-qt`` → the pipeline's GUI smoke test: create the
  application (offscreen), apply the theme, build the real main
  window, and construct the course web view — if the packaged GUI
  would die on launch, it dies in CI, not on a customer's machine.
- ``--version`` → print the version and exit.
- anything else (including no arguments) → the app: what a person
  double-clicking the file gets.

Routing is pure and unit-tested; the heavy halves (Qt) are
imported only on the branch that needs them.
"""

from __future__ import annotations

import importlib
import sys

from . import __version__

#: The import census for ``--self-check``: every module the
#: packaged executable loads lazily at runtime. PyInstaller's
#: static analysis follows imports it can SEE; the Qt layer and
#: the web engine are imported inside the GUI package by design,
#: so they are exactly what a build can silently ship without.
#: The release workflow runs the built exe with ``--self-check``
#: and fails the release if any name here cannot be imported.
SELF_CHECK_MODULES = (
    # Qt stack (the whole chrome)
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    # The embedded browser (course rendering + exam)
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    # HackProof's own lazy halves
    "hackproof_app.config",
    "hackproof_app.license_keys",
    "hackproof_app.service_client",
    "hackproof_app.proxy_logic",
    "hackproof_app.site_bundle",
    "hackproof_app.setup_engine",
    "hackproof_app.gui.theme",
    "hackproof_app.gui.webview",
    "hackproof_app.gui.premium_page",
    "hackproof_app.gui.setup_app",
    "hackproof_app.gui.main_window",
    "hackproof_app.gui.app",
)


def run_self_check(import_module=None) -> int:
    """Import every module in :data:`SELF_CHECK_MODULES`.

    Prints the product version and the census result. Returns 0
    when everything imports; returns 1 and names each failing
    module (on stderr) otherwise. Opens no window.
    """
    importer = import_module or importlib.import_module
    failures: list[tuple[str, BaseException]] = []
    for name in SELF_CHECK_MODULES:
        try:
            importer(name)
        except BaseException as exc:  # named, counted — never hidden
            failures.append((name, exc))
    if failures:
        for name, exc in failures:
            print(
                f"hackproof self-check: FAILED to import {name}: {exc!r}",
                file=sys.stderr,
            )
        print(
            f"HackProof {__version__} self-check FAILED: "
            f"{len(failures)} of {len(SELF_CHECK_MODULES)} modules "
            "could not be imported.",
            file=sys.stderr,
        )
        return 1
    print(
        f"HackProof {__version__} self-check OK: "
        f"{len(SELF_CHECK_MODULES)} modules imported."
    )
    return 0


def _default_qt_app():
    """Build the real QApplication for the Qt self-check (offscreen
    by default — the check runs headless in the release pipeline,
    and the platform plugin is exactly what it exists to catch)."""
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication(
        [sys.argv[0] or "HackProof.exe"]
    )


def _default_qt_window(app):
    """Theme *app* and build the real main window on it, then
    construct the course web view once — importing QtWebEngine is
    not proof its process and resources shipped; building the view
    is. Returns the window."""
    from .gui import theme
    from .gui.main_window import MainWindow

    theme.apply_theme(app)
    window = MainWindow()
    view = window.ensure_web_view("course")
    if view is not None:
        view.show()
    return window


def run_self_check_qt(app_factory=None, window_factory=None) -> int:
    """Prove the packaged GUI can actually start, not just import.

    Returns 0 on success; returns 1 with a plain message naming
    the stage that failed otherwise. *app_factory* /
    *window_factory* are the injectable seam the tests use;
    production passes neither and gets the real stack.
    """
    make_app = app_factory or _default_qt_app
    build_window = window_factory or _default_qt_window

    try:
        app = make_app()
    except BaseException as exc:  # named, staged — never hidden
        print(
            "hackproof Qt self-check: FAILED to create the Qt "
            f"application: {exc!r}",
            file=sys.stderr,
        )
        print(
            f"HackProof {__version__} Qt self-check FAILED: the "
            "interface could not start (the Qt platform plugin may "
            "be missing from this build).",
            file=sys.stderr,
        )
        return 1

    try:
        window = build_window(app)
        window.show()
        if hasattr(app, "processEvents"):
            app.processEvents()
        window.close()
        if hasattr(app, "processEvents"):
            app.processEvents()
    except BaseException as exc:  # named, staged — never hidden
        print(
            "hackproof Qt self-check: FAILED to build or show the "
            f"main window: {exc!r}",
            file=sys.stderr,
        )
        print(
            f"HackProof {__version__} Qt self-check FAILED: the "
            "application started but its main window could not be "
            "built.",
            file=sys.stderr,
        )
        return 1

    print(
        f"HackProof {__version__} Qt self-check OK: application "
        "created, theme applied, main window built, course web "
        "view constructed."
    )
    return 0


def route_invocation(argv: list[str]) -> str:
    """Classify one launch. *argv* excludes the program name.

    Returns one of: ``"setup"``, ``"uninstall"``, ``"self-check"``,
    ``"self-check-qt"``, ``"version"``, ``"gui"``.
    """
    args = [str(a) for a in argv]
    if "--run-setup" in args:
        return "setup"
    if "--uninstall" in args:
        return "uninstall"
    if "--self-check-qt" in args:
        return "self-check-qt"
    if "--self-check" in args:
        return "self-check"
    if "--version" in args:
        return "version"
    return "gui"


def main(argv: list[str] | None = None) -> int:
    """Dispatch one launch of the packaged executable."""
    args = list(sys.argv[1:] if argv is None else argv)
    route = route_invocation(args)

    if route == "setup":
        from .gui.setup_app import run_setup

        return run_setup()

    if route == "uninstall":
        from .gui.setup_app import run_uninstall

        return run_uninstall()

    if route == "self-check-qt":
        return run_self_check_qt()

    if route == "self-check":
        return run_self_check()

    if route == "version":
        print(f"HackProof {__version__}")
        return 0

    from .gui import app as gui_app

    return gui_app.run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
