"""Launch routing and the CI smoke checks (the Argus entry
pattern): pure routing, the import census with an injected
importer, the Qt check with injected factories, and main()'s
dispatch through module fakes."""

from __future__ import annotations

import sys
import types

import pytest

from hackproof_app import __version__, entry


@pytest.mark.parametrize("argv,expected", [
    (["--run-setup"], "setup"),
    (["--uninstall"], "uninstall"),
    (["--self-check"], "self-check"),
    (["--self-check-qt"], "self-check-qt"),
    (["--version"], "version"),
    ([], "gui"),
    (["some-file.html"], "gui"),
    (["--run-setup", "--self-check"], "setup"),  # setup wins
])
def test_route_invocation(argv, expected):
    assert entry.route_invocation(argv) == expected


def _importer(failing=()):
    def import_module(name):
        if name in failing:
            raise ImportError(f"no {name}")
        return types.ModuleType(name)

    return import_module


def test_self_check_all_import(capsys):
    assert entry.run_self_check(import_module=_importer()) == 0
    assert "self-check OK" in capsys.readouterr().out


def test_self_check_names_failures(capsys):
    code = entry.run_self_check(
        import_module=_importer({"PySide6.QtWebEngineWidgets"})
    )
    assert code == 1
    err = capsys.readouterr().err
    assert "PySide6.QtWebEngineWidgets" in err


class FakeApp:
    def __init__(self):
        self.events = 0

    def processEvents(self):  # noqa: N802 (Qt name)
        self.events += 1


class FakeWindow:
    def __init__(self):
        self.shown = False
        self.closed = False

    def show(self):
        self.shown = True

    def close(self):
        self.closed = True


def test_qt_check_with_injected_factories():
    window = FakeWindow()
    code = entry.run_self_check_qt(
        app_factory=FakeApp,
        window_factory=lambda app: window,
    )
    assert code == 0
    assert window.shown and window.closed


def test_qt_check_failures_are_staged(capsys):
    def bad_app():
        raise RuntimeError("no platform plugin")

    assert entry.run_self_check_qt(app_factory=bad_app) == 1
    assert "FAILED" in capsys.readouterr().err

    def bad_window(app):
        raise RuntimeError("no engine")

    assert entry.run_self_check_qt(
        app_factory=FakeApp, window_factory=bad_window
    ) == 1


def test_main_version(capsys):
    assert entry.main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_main_dispatches_setup_and_gui(monkeypatch):
    setup_mod = types.ModuleType("hackproof_app.gui.setup_app")
    setup_mod.run_setup = lambda: 11
    setup_mod.run_uninstall = lambda: 12
    monkeypatch.setitem(sys.modules, "hackproof_app.gui.setup_app", setup_mod)
    assert entry.main(["--run-setup"]) == 11
    assert entry.main(["--uninstall"]) == 12

    gui_mod = types.ModuleType("hackproof_app.gui.app")
    seen = {}

    def run_gui(argv):
        seen["argv"] = argv
        return 13

    gui_mod.run_gui = run_gui
    monkeypatch.setitem(sys.modules, "hackproof_app.gui.app", gui_mod)
    assert entry.main(["anything"]) == 13
    assert seen["argv"] == ["anything"]


def test_main_self_check_flags_use_entry_runners(monkeypatch):
    monkeypatch.setattr(entry, "run_self_check", lambda: 5)
    monkeypatch.setattr(entry, "run_self_check_qt", lambda: 6)
    assert entry.main(["--self-check"]) == 5
    assert entry.main(["--self-check-qt"]) == 6
