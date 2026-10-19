"""Self-install engine: the one HackProof executable sets itself up.

Mirrors the ARGUS.EXE v1.1.0 pattern (``argus/setup_engine.py``),
trimmed to what a course app needs — there is no protection
service to install and no Security Center registration here:

1. places the executable at its canonical home
   (``C:\\Program Files\\Sentinel Safeguard\\HackProof\\HackProof.exe``),
   verifying the copy byte-for-byte;
2. writes the Apps & Features (Add/Remove Programs) entry — its
   UninstallString runs this same exe with ``--uninstall``;
3. creates the Start Menu shortcut;
4. VERIFIES — the placed file's hash matches, the entry and the
   shortcut are positively present — before calling setup done.

Every step is checked and every failure raises :class:`SetupError`
carrying a plain-language ``user_message`` (the only text a user
ever sees) plus a technical ``detail`` for logs and support. No
step's failure is swallowed: Argus v1.0.5 shipped "installed" with
nothing installed because a hidden step failed silently — that
failure mode is designed out here, the same way it was there.

The GUI also runs fine WITHOUT installing (a deliberate divergence
from Argus: nothing privileged needs setting up for a course, so
install is an offer, never a gate).

All machine-touching operations are injectable seams (keyword
arguments), so the whole engine is unit-tested off Windows.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from . import __version__ as APP_VERSION
from . import config

IS_WINDOWS = sys.platform == "win32"

#: Where the one executable lives once installed.
INSTALL_FOLDER_PARTS = ("Sentinel Safeguard", "HackProof")
EXE_NAME = "HackProof.exe"

#: Add/Remove Programs registry key (HKLM) for the installed product.
UNINSTALL_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\HackProof"
)
UNINSTALL_DISPLAY_NAME = "HackProof — Sentinel Safeguard"
UNINSTALL_PUBLISHER = "Sentinel Safeguard LLC"

#: Start Menu location (all users), mirroring Argus.
START_MENU_PARTS = ("Microsoft", "Windows", "Start Menu", "Programs",
                    "Sentinel Safeguard")

#: The setup result the elevated helper leaves for the GUI.
SETUP_RESULT_NAME = "setup-result.json"

#: Progress step keys, in order. The setup window maps these to
#: plain-language lines; the engine never invents others.
STEP_PLACING = "placing"
STEP_REGISTERING = "registering"
STEP_SHORTCUTS = "shortcuts"
STEP_VERIFYING = "verifying"


class SetupState(Enum):
    """What setup can know about this machine."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    INSTALLED_INCOMPLETE = "installed_incomplete"
    PORTABLE = "portable"


class SetupError(RuntimeError):
    """A setup step failed, in two voices (Argus's contract)."""

    def __init__(self, user_message: str, detail: str = ""):
        super().__init__(user_message)
        self.user_message = user_message
        self.detail = detail


# ----------------------------------------------------------------------
# Locations & state
# ----------------------------------------------------------------------
def canonical_install_dir() -> Path:
    program_files = os.environ.get("ProgramFiles") or r"C:\Program Files"
    return Path(program_files).joinpath(*INSTALL_FOLDER_PARTS)


def canonical_exe_path() -> Path:
    return canonical_install_dir() / EXE_NAME


def start_menu_folder() -> Path:
    program_data = os.environ.get("ProgramData") or r"C:\ProgramData"
    return Path(program_data).joinpath(*START_MENU_PARTS)


def start_menu_shortcut() -> Path:
    return start_menu_folder() / "HackProof.lnk"


def _running_exe() -> Path | None:
    """The file currently running, when it is a packaged exe.
    Source checkouts (python.exe) return None — nothing to place."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return None


def _arp_entry_present() -> bool:
    """True when the Apps & Features entry exists — or when the
    question cannot be answered here (off Windows it cannot, and
    an unanswerable probe never demotes a healthy install)."""
    if not IS_WINDOWS:
        return True
    try:
        import winreg  # type: ignore[import-not-found]

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY, 0, winreg.KEY_READ
        ):
            return True
    except FileNotFoundError:
        return False  # provably missing
    except Exception:
        return True  # unanswerable ≠ missing


def _arp_entry_verified() -> bool:
    """Strict variant for install(): True only when the entry is
    POSITIVELY seen. Re-writing is idempotent; skipping on a guess
    is how partial installs stay partial."""
    if not IS_WINDOWS:
        return False
    try:
        import winreg  # type: ignore[import-not-found]

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY, 0, winreg.KEY_READ
        ):
            return True
    except Exception:
        return False


def detect_state(
    *,
    portable: bool | None = None,
    exe_present: bool | None = None,
    arp_present: bool | None = None,
    shortcut_present: bool | None = None,
) -> SetupState:
    """Classify this machine for the GUI's setup states.

    A canonical exe that exists WITHOUT its Apps & Features entry
    or Start Menu shortcut provably present is
    :attr:`SetupState.INSTALLED_INCOMPLETE` — a partial install
    (interrupted, or from an older setup) that re-running setup
    heals.
    """
    if config.is_portable() if portable is None else portable:
        return SetupState.PORTABLE
    if exe_present is None:
        exe_present = canonical_exe_path().is_file()
    if not exe_present:
        return SetupState.NOT_INSTALLED
    if arp_present is None:
        arp_present = _arp_entry_present()
    if shortcut_present is None:
        shortcut_present = start_menu_shortcut().is_file()
    if not arp_present or not shortcut_present:
        return SetupState.INSTALLED_INCOMPLETE
    return SetupState.INSTALLED


# ----------------------------------------------------------------------
# Elevation
# ----------------------------------------------------------------------
def is_elevated() -> bool:
    """True when this process runs with an administrator token."""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False


def relaunch_as_admin(
    arguments: list[str], *, exe: Path | str | None = None
) -> bool:
    """Relaunch a HackProof executable elevated (the one familiar
    UAC prompt). True when Windows accepted the launch; False when
    the person declined or the launch failed — the caller shows
    the designed "needs your permission" state either way."""
    if not IS_WINDOWS:
        return False
    try:
        import ctypes

        target = str(exe) if exe is not None else sys.executable
        params = " ".join(
            f'"{arg}"' if any(c in arg for c in " \t") else arg
            for arg in arguments
        )
        result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None, "runas", target, params, None, 1
        )
        return int(result) > 32
    except Exception:
        return False


# ----------------------------------------------------------------------
# Setup result hand-off (elevated helper → GUI)
# ----------------------------------------------------------------------
def setup_result_path() -> Path:
    return config.data_dir() / SETUP_RESULT_NAME


def write_setup_result(result: dict) -> Path:
    payload = dict(result)
    payload.setdefault("at", time.time())
    return config.write_text_atomic(
        setup_result_path(), json.dumps(payload, indent=2)
    )


def read_setup_result(*, max_age_seconds: float = 600.0) -> dict | None:
    """The last setup outcome, when one was left recently."""
    try:
        raw = json.loads(setup_result_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    at = raw.get("at")
    if isinstance(at, (int, float)) and time.time() - at > max_age_seconds:
        return None
    return raw


# ----------------------------------------------------------------------
# Command seam + file helpers
# ----------------------------------------------------------------------
def _default_run_command(argv: list[str]):
    return subprocess.run(argv, capture_output=True, text=True)


def _run_checked(run_command, argv: list[str], user_message: str) -> None:
    try:
        completed = run_command(argv)
    except OSError as exc:
        raise SetupError(user_message, detail=repr(exc)) from exc
    if getattr(completed, "returncode", 0) != 0:
        raise SetupError(
            user_message,
            detail=f"{argv[0]} exited {completed.returncode}: "
                   f"{(completed.stderr or '')[:400]}",
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return a.resolve() == b.resolve()


# ----------------------------------------------------------------------
# Registration steps (default implementations; tests inject fakes)
# ----------------------------------------------------------------------
def _write_uninstall_entry(exe: Path) -> None:
    import winreg  # type: ignore[import-not-found]

    with winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY, 0, winreg.KEY_WRITE
    ) as key:
        winreg.SetValueEx(
            key, "DisplayName", 0, winreg.REG_SZ, UNINSTALL_DISPLAY_NAME
        )
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, UNINSTALL_PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ,
                          str(exe.parent))
        winreg.SetValueEx(
            key, "UninstallString", 0, winreg.REG_SZ, f'"{exe}" --uninstall'
        )
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe))
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)


def _remove_uninstall_entry() -> None:
    import winreg  # type: ignore[import-not-found]

    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, UNINSTALL_KEY)
    except FileNotFoundError:
        pass  # already gone — the desired end state


def _create_start_menu_shortcut(exe: Path, run_command) -> None:
    """Create the Start Menu shortcut through the shell —
    PowerShell's WScript.Shell COM is the scriptable route,
    exit-code-checked like every other step (Argus's pattern)."""
    folder = start_menu_folder()
    link = start_menu_shortcut()
    script = "; ".join(
        [
            f"New-Item -ItemType Directory -Force '{folder}' | Out-Null",
            "$ws = New-Object -ComObject WScript.Shell",
            f"$s = $ws.CreateShortcut('{link}'); "
            f"$s.TargetPath = '{exe}'; $s.Save()",
        ]
    )
    _run_checked(
        run_command,
        ["powershell.exe", "-NoProfile", "-NonInteractive",
         "-Command", script],
        "HackProof couldn't create its Start Menu shortcut. "
        "Try setting up again.",
    )


def _remove_start_menu_shortcut() -> None:
    try:
        start_menu_shortcut().unlink()
    except FileNotFoundError:
        pass
    try:
        start_menu_folder().rmdir()  # only when empty
    except OSError:
        pass


# ----------------------------------------------------------------------
# Install
# ----------------------------------------------------------------------
@dataclass
class InstallResult:
    state: SetupState
    exe: Path
    steps: list[str] = field(default_factory=list)


def install(
    *,
    progress=None,
    source_exe: Path | None = None,
    target_exe: Path | None = None,
    run_command=None,
    write_arp=None,
    create_shortcut=None,
    verify_arp=None,
) -> InstallResult:
    """Place HackProof at its canonical home and register it.

    Idempotent and resumable: a machine already INSTALLED returns
    at once; a partial install is healed by re-running the missing
    steps. Raises :class:`SetupError` at the first failed step —
    nothing is claimed that was not verified.
    """
    run = run_command or _default_run_command
    emit = progress or (lambda _step: None)
    source = source_exe or _running_exe()
    target = target_exe or canonical_exe_path()
    if source is None:
        raise SetupError(
            "This copy of HackProof can't set itself up. Download "
            "HackProof again and run the downloaded file.",
            detail="not running from a packaged executable",
        )
    steps: list[str] = []

    # 1) Placing: copy self to the canonical home, byte-verified.
    emit(STEP_PLACING)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not (target.is_file() and _same_file(source, target)):
            shutil.copyfile(source, target)
        if _sha256(source) != _sha256(target):
            raise SetupError(
                "The copied program didn't check out. Try setting "
                "up again — if it keeps happening, download "
                "HackProof once more.",
                detail="SHA-256 of placed exe differs from source",
            )
    except SetupError:
        raise
    except OSError as exc:
        raise SetupError(
            "HackProof couldn't put itself in place. Try setting "
            "up again.",
            detail=repr(exc),
        ) from exc
    steps.append(STEP_PLACING)

    # 2) Registering: the Apps & Features entry.
    emit(STEP_REGISTERING)
    try:
        (write_arp or _write_uninstall_entry)(target)
    except Exception as exc:
        raise SetupError(
            "HackProof couldn't register itself with Windows. "
            "Try setting up again.",
            detail=repr(exc),
        ) from exc
    steps.append(STEP_REGISTERING)

    # 3) Start Menu shortcut.
    emit(STEP_SHORTCUTS)
    try:
        if create_shortcut is not None:
            create_shortcut(target)
        else:
            _create_start_menu_shortcut(target, run)
    except SetupError:
        raise
    except Exception as exc:
        raise SetupError(
            "HackProof couldn't create its Start Menu shortcut. "
            "Try setting up again.",
            detail=repr(exc),
        ) from exc
    steps.append(STEP_SHORTCUTS)

    # 4) Verifying: everything claimed must be positively present.
    emit(STEP_VERIFYING)
    arp_ok = (verify_arp or _arp_entry_verified)()
    problems = []
    if not target.is_file():
        problems.append("placed exe missing")
    if not arp_ok:
        problems.append("Apps & Features entry not verifiable")
    if not start_menu_shortcut().is_file() and create_shortcut is None:
        problems.append("Start Menu shortcut missing")
    if problems:
        raise SetupError(
            "Setup finished but a check didn't pass, so HackProof "
            "isn't calling this done. Run setup once more; if it "
            "keeps happening, contact Sentinel Safeguard.",
            detail="; ".join(problems),
        )
    steps.append(STEP_VERIFYING)

    return InstallResult(
        state=SetupState.INSTALLED, exe=target, steps=steps
    )


# ----------------------------------------------------------------------
# Uninstall
# ----------------------------------------------------------------------
@dataclass
class UninstallResult:
    steps: list[str] = field(default_factory=list)
    removed_data: bool = False
    leftovers: list[str] = field(default_factory=list)


def uninstall(
    *,
    remove_data: bool = False,
    progress=None,
    target_exe: Path | None = None,
    remove_arp=None,
    remove_shortcut=None,
    data_directory: Path | None = None,
) -> UninstallResult:
    """Remove HackProof: entry, shortcut, program, and (only when
    asked) the person's data. Honest about leftovers — a running
    exe cannot delete itself, so its removal is scheduled for the
    next restart and reported, never hidden."""
    emit = progress or (lambda _step: None)
    target = target_exe or canonical_exe_path()
    result = UninstallResult()

    emit("removing-entry")
    try:
        (remove_arp or _remove_uninstall_entry)()
    except Exception:
        result.leftovers.append(
            "the Apps & Features entry couldn't be removed"
        )
    result.steps.append("removing-entry")

    emit("removing-shortcut")
    try:
        (remove_shortcut or _remove_start_menu_shortcut)()
    except Exception:
        result.leftovers.append("the Start Menu shortcut is still there")
    result.steps.append("removing-shortcut")

    emit("removing-program")
    running = _running_exe()
    try:
        if target.is_file():
            target.unlink()
    except OSError:
        # Very likely because THIS process is running from it.
        _schedule_delete_on_reboot(target)
        result.leftovers.append(
            "the program file itself will be removed when this PC "
            "restarts"
        )
    try:
        target.parent.rmdir()
    except OSError:
        pass
    result.steps.append("removing-program")

    if remove_data:
        emit("removing-data")
        folder = data_directory or config.data_dir()
        try:
            shutil.rmtree(folder)
            result.removed_data = True
        except FileNotFoundError:
            result.removed_data = True
        except OSError:
            result.leftovers.append(
                "your HackProof data (settings and saved key) "
                "couldn't be fully removed"
            )
        result.steps.append("removing-data")

    _ = running  # (kept for parity with Argus's result accounting)
    return result


def _schedule_delete_on_reboot(path: Path) -> None:
    """Ask Windows to delete *path* at the next restart
    (MoveFileEx with MOVEFILE_DELAY_UNTIL_REBOOT)."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes

        ctypes.windll.kernel32.MoveFileExW(  # type: ignore[attr-defined]
            str(path), None, 0x4
        )
    except Exception:
        pass
