"""The install engine against its injectable seams: state
classification, the four-step install (byte-verified placing),
resumability after a mid-install failure, uninstall keeping data
unless asked, and the setup-result hand-off file."""

from __future__ import annotations

import hashlib

import pytest

from hackproof_app import setup_engine
from hackproof_app.setup_engine import SetupError, SetupState

EXE_BYTES = b"MZ-fake-hackproof-exe" * 64


@pytest.fixture()
def rig(tmp_path):
    class Rig:
        def __init__(self):
            self.source = tmp_path / "download" / "HackProof.exe"
            self.source.parent.mkdir(parents=True)
            self.source.write_bytes(EXE_BYTES)
            self.target = (
                tmp_path / "Program Files" / "Sentinel Safeguard"
                / "HackProof" / "HackProof.exe"
            )
            self.arp_written_for = None
            self.shortcut_for = None
            self.arp_verified = False

        def write_arp(self, exe):
            self.arp_written_for = exe
            self.arp_verified = True

        def create_shortcut(self, exe):
            self.shortcut_for = exe

    return Rig()


def install(rig, **overrides):
    kwargs = dict(
        source_exe=rig.source,
        target_exe=rig.target,
        write_arp=rig.write_arp,
        create_shortcut=rig.create_shortcut,
        verify_arp=lambda: rig.arp_verified,
    )
    kwargs.update(overrides)
    return setup_engine.install(**kwargs)


# ------------------------------------------------------------- states


def test_detect_state_matrix():
    d = setup_engine.detect_state
    assert d(portable=True) is SetupState.PORTABLE
    assert d(portable=False, exe_present=False) is SetupState.NOT_INSTALLED
    assert d(portable=False, exe_present=True, arp_present=True,
             shortcut_present=True) is SetupState.INSTALLED
    assert d(portable=False, exe_present=True, arp_present=False,
             shortcut_present=True) is SetupState.INSTALLED_INCOMPLETE
    assert d(portable=False, exe_present=True, arp_present=True,
             shortcut_present=False) is SetupState.INSTALLED_INCOMPLETE


# ------------------------------------------------------------ install


def test_install_happy_path(rig):
    steps = []
    result = install(rig, progress=steps.append)
    assert result.state is SetupState.INSTALLED
    assert result.exe == rig.target
    assert rig.target.read_bytes() == EXE_BYTES
    assert hashlib.sha256(rig.target.read_bytes()).hexdigest() == \
        hashlib.sha256(EXE_BYTES).hexdigest()
    assert rig.arp_written_for == rig.target
    assert rig.shortcut_for == rig.target
    assert steps == [
        setup_engine.STEP_PLACING, setup_engine.STEP_REGISTERING,
        setup_engine.STEP_SHORTCUTS, setup_engine.STEP_VERIFYING,
    ]
    assert result.steps == steps


def test_install_idempotent_second_run(rig):
    install(rig)
    result = install(rig)  # same bytes: no complaint, still verified
    assert result.state is SetupState.INSTALLED


def test_install_requires_a_packaged_source(rig):
    with pytest.raises(SetupError) as exc:
        setup_engine.install(source_exe=None, target_exe=rig.target)
    assert "can't set itself up" in exc.value.user_message


def test_install_failure_is_resumable(rig):
    calls = {"n": 0}

    def flaky_arp(exe):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("registry busy")
        rig.arp_verified = True

    with pytest.raises(SetupError):
        install(rig, write_arp=flaky_arp)
    # The placed exe is there but unregistered: exactly the
    # INCOMPLETE state the GUI offers to heal.
    assert rig.target.is_file()
    assert setup_engine.detect_state(
        portable=False, exe_present=True, arp_present=False,
        shortcut_present=True,
    ) is SetupState.INSTALLED_INCOMPLETE
    result = install(rig, write_arp=flaky_arp)
    assert result.state is SetupState.INSTALLED


def test_install_verification_refuses_unverifiable(rig):
    with pytest.raises(SetupError) as exc:
        install(rig, verify_arp=lambda: False)
    assert "isn't calling this done" in exc.value.user_message


# ---------------------------------------------------------- uninstall


def test_uninstall_removes_program_keeps_data(rig, tmp_path):
    install(rig)
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text("{}", encoding="utf-8")
    removed = []
    result = setup_engine.uninstall(
        target_exe=rig.target,
        remove_arp=lambda: removed.append("arp"),
        remove_shortcut=lambda: removed.append("shortcut"),
        data_directory=data,
    )
    assert removed == ["arp", "shortcut"]
    assert not rig.target.exists()
    assert (data / "settings.json").exists()  # kept by default
    assert not result.removed_data
    assert result.leftovers == []


def test_uninstall_remove_data_only_when_asked(rig, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "settings.json").write_text("{}", encoding="utf-8")
    result = setup_engine.uninstall(
        target_exe=rig.target,
        remove_arp=lambda: None,
        remove_shortcut=lambda: None,
        remove_data=True,
        data_directory=data,
    )
    assert result.removed_data
    assert not data.exists()


def test_uninstall_failures_become_leftovers_not_crashes(rig):
    def boom():
        raise OSError("locked")

    result = setup_engine.uninstall(
        target_exe=rig.target, remove_arp=boom, remove_shortcut=boom,
    )
    assert len(result.leftovers) == 2
    assert "removing-entry" in result.steps


# ------------------------------------------------------- result file


def test_result_file_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("HACKPROOF_DATA_DIR", str(tmp_path))
    setup_engine.write_setup_result({"ok": True, "message": "done"})
    result = setup_engine.read_setup_result()
    assert result["ok"] is True and result["message"] == "done"
    assert "at" in result  # timestamped by the writer
    stale = setup_engine.read_setup_result(max_age_seconds=-1)
    assert stale is None


@pytest.mark.skipif(
    setup_engine.IS_WINDOWS,
    reason="the off-Windows contract; Windows behavior is covered "
           "by test_elevation_helpers_on_windows",
)
def test_elevation_helpers_are_safe_off_windows():
    # Off Windows both must answer cleanly, never raise.
    assert setup_engine.is_elevated() is False
    assert setup_engine.relaunch_as_admin(["--run-setup"]) is False


@pytest.mark.skipif(
    not setup_engine.IS_WINDOWS,
    reason="Windows-only: exercises the real ShellExecuteW boundary",
)
def test_elevation_helpers_on_windows(monkeypatch):
    # is_elevated() reads the process token: whatever it is on
    # this machine (CI runners run elevated; a normal customer
    # session usually is not), it must answer a plain bool and
    # never raise.
    assert isinstance(setup_engine.is_elevated(), bool)
    # relaunch_as_admin() maps ShellExecuteW's return: > 32 means
    # Windows accepted the launch, <= 32 means refused/failed.
    # Stub the boundary so the test launches nothing.
    import ctypes

    shell32 = ctypes.windll.shell32  # type: ignore[attr-defined]
    monkeypatch.setattr(
        shell32, "ShellExecuteW", lambda *args: 33, raising=False
    )
    assert setup_engine.relaunch_as_admin(["--run-setup"]) is True
    monkeypatch.setattr(
        shell32, "ShellExecuteW", lambda *args: 5, raising=False
    )
    assert setup_engine.relaunch_as_admin(["--run-setup"]) is False
