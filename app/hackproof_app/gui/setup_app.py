"""The setup and uninstall flows of the one-executable product.

These run in their own (elevated) process (the ARGUS.EXE pattern):
the app relaunches the same HackProof.exe with ``--run-setup`` or
``--uninstall`` and Windows shows its one familiar permission
prompt. What the person sees is deliberately tiny — a short
progress window that tells the truth step by step, then either
"all done" or one plain sentence about what went wrong and what
to do next. Technical detail goes to the setup result file and
the log, never the screen.
"""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .. import setup_engine
from ..setup_engine import SetupError
from . import theme


def _themed_app() -> QApplication:
    """The QApplication for these flows, with the full theme —
    they run in their own process and must not come up in a
    default light palette while the rest of HackProof is dark."""
    app = QApplication.instance() or QApplication([])
    theme.apply_theme(app)
    return app


log = logging.getLogger("hackproof.setup")

STEP_LABELS = {
    setup_engine.STEP_PLACING: "Putting HackProof in place…",
    setup_engine.STEP_REGISTERING: "Registering HackProof with Windows…",
    setup_engine.STEP_SHORTCUTS: "Adding the Start Menu shortcut…",
    setup_engine.STEP_VERIFYING: "Checking everything is really in place…",
    "removing-entry": "Removing the Apps & Features entry…",
    "removing-shortcut": "Removing the Start Menu shortcut…",
    "removing-program": "Removing the HackProof program…",
    "removing-data": "Removing your HackProof data…",
}


class _Bridge(QObject):
    step = Signal(str)
    finished = Signal(object)  # (result, error)


class ProgressDialog(QDialog):
    """One heading, one status line, one button that enables at
    the end. Close-hardened while work runs (Argus's rule): a
    close attempt mid-setup is ignored with an honest sentence —
    closing would strand exactly the half-set-up state the
    resumable engine then has to heal."""

    def __init__(self, title: str, first_line: str, parent=None):
        super().__init__(parent)
        self._running = True
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        self.heading = QLabel(first_line)
        self.heading.setWordWrap(True)
        self.heading.setObjectName("Headline")
        layout.addWidget(self.heading)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("Subhead")
        layout.addWidget(self.status_label)
        self.done_button = QPushButton("Done")
        self.done_button.setObjectName("Primary")
        self.done_button.setEnabled(False)
        self.done_button.clicked.connect(self.accept)
        layout.addWidget(self.done_button)

    def show_step(self, step_key: str) -> None:
        self.status_label.setText(STEP_LABELS.get(step_key, "Working…"))

    def _defer_close(self) -> None:
        self.status_label.setText(
            "Still working — please wait for this to finish. "
            "Closing now could leave HackProof half set up."
        )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt name)
        if self._running:
            event.ignore()
            self._defer_close()
            return
        super().closeEvent(event)

    def reject(self) -> None:
        if self._running:
            self._defer_close()
            return
        super().reject()

    def finish_ok(self, message: str) -> None:
        self._running = False
        self.heading.setText(message)
        self.status_label.setText("")
        self.done_button.setEnabled(True)

    def finish_error(self, message: str) -> None:
        self._running = False
        self.heading.setText("Something needs your attention")
        self.status_label.setText(message)
        self.done_button.setText("Close")
        self.done_button.setEnabled(True)


def _write_result_safe(payload: dict) -> None:
    """Write the result hand-off file, guarded: a failure to write
    it must never mask the outcome the dialog is showing."""
    try:
        setup_engine.write_setup_result(payload)
    except Exception:
        log.exception("could not write the setup result file")


def _run_with_progress(title, first_line, work, on_result) -> int:
    app = _themed_app()
    dialog = ProgressDialog(title, first_line)
    bridge = _Bridge()

    def _dispatch(payload):
        result, error = payload
        on_result(dialog, result, error)

    bridge.step.connect(dialog.show_step)
    bridge.finished.connect(_dispatch)

    def target():
        try:
            result = work(bridge.step.emit)
        except SetupError as exc:
            bridge.finished.emit((None, exc))
        except Exception as exc:  # never a traceback window
            log.exception("setup flow failed unexpectedly")
            bridge.finished.emit(
                (
                    None,
                    SetupError(
                        "Something unexpected went wrong. Try again; "
                        "if it keeps happening, contact Sentinel "
                        "Safeguard.",
                        detail=repr(exc),
                    ),
                )
            )
        else:
            bridge.finished.emit((result, None))

    threading.Thread(target=target, name="hackproof-setup",
                     daemon=True).start()
    dialog.show()
    return app.exec()


def run_setup() -> int:
    """``--run-setup``: the elevated half of "Install HackProof"."""
    if not setup_engine.is_elevated():
        if setup_engine.relaunch_as_admin(["--run-setup"]):
            return 0
        _write_result_safe(
            {
                "ok": False,
                "needs_permission": True,
                "message": (
                    "HackProof needs your permission to finish "
                    "setting up. Choose “Install” and allow the "
                    "Windows prompt to continue."
                ),
                "detail": "elevation declined before setup started",
            }
        )
        return 1

    def work(progress):
        return setup_engine.install(progress=progress)

    def on_result(dialog, result, error):
        if error is not None:
            _write_result_safe(
                {"ok": False, "message": error.user_message,
                 "detail": error.detail}
            )
            log.error("setup failed: %s (%s)",
                      error.user_message, error.detail)
            dialog.finish_error(error.user_message)
            return
        _write_result_safe(
            {"ok": True, "state": result.state.value,
             "message": "HackProof is installed."}
        )
        dialog.finish_ok(
            "All done — HackProof is installed. You'll find it in "
            "your Start Menu and in Apps & Features."
        )

    return _run_with_progress(
        "Setting up HackProof", "Setting up HackProof…", work, on_result
    )


def run_uninstall() -> int:
    """``--uninstall``: confirm plainly, then remove HackProof."""
    if not setup_engine.is_elevated():
        # Declining the prompt simply aborts — normal Windows
        # behavior, nothing to explain.
        setup_engine.relaunch_as_admin(["--uninstall"])
        return 0

    app = _themed_app()
    confirm = QDialog()
    confirm.setWindowTitle("Remove HackProof")
    confirm.setMinimumWidth(440)
    layout = QVBoxLayout(confirm)
    heading = QLabel("Remove HackProof from this PC?")
    heading.setObjectName("Headline")
    heading.setWordWrap(True)
    layout.addWidget(heading)
    body = QLabel(
        "The program, its Start Menu shortcut, and its Apps & "
        "Features entry will be removed. You can reinstall "
        "HackProof at any time — your license key keeps working."
    )
    body.setWordWrap(True)
    body.setObjectName("Subhead")
    layout.addWidget(body)
    remove_data = QCheckBox(
        "Also remove my HackProof data — settings and my saved "
        "license key"
    )
    remove_data.setChecked(False)  # data is kept unless asked for
    layout.addWidget(remove_data)
    remove_button = QPushButton("Remove HackProof")
    remove_button.setObjectName("Primary")
    cancel_button = QPushButton("Cancel")
    remove_button.clicked.connect(confirm.accept)
    cancel_button.clicked.connect(confirm.reject)
    layout.addWidget(remove_button)
    layout.addWidget(cancel_button)
    if confirm.exec() != QDialog.DialogCode.Accepted:
        return 0
    wipe = remove_data.isChecked()

    def work(progress):
        return setup_engine.uninstall(remove_data=wipe, progress=progress)

    def on_result(dialog, result, error):
        if error is not None:
            log.error("uninstall failed: %s (%s)",
                      error.user_message, error.detail)
            dialog.finish_error(error.user_message)
            return
        message = "HackProof has been removed."
        if result.leftovers:
            message += "\n\nOne note: " + "; ".join(result.leftovers) + "."
        dialog.finish_ok(message)

    return _run_with_progress(
        "Removing HackProof", "Removing HackProof…", work, on_result
    )
