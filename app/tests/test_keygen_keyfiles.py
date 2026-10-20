"""Key-file handling in tools/keygen.py: the setup -> load
round-trip must survive Windows.

cmd_setup writes RAW key material (32 bytes each) through
os.open/os.write. On Windows an os.open without O_BINARY yields a
CRT text-mode descriptor, and every 0x0A byte in the material is
stored as 0x0D 0x0A. load_keys reads the files back in binary
("rb"), so the inflated length trips its "expected 32 bytes each"
refusal. Whether a given setup fails is a coin flip on the drawn
bytes (a 32-byte key contains a 0x0A with probability ~12%, so
~22% of setups have at least one bad file) — that is exactly how
the app-v1.0.3 Windows builds died while Linux stayed green, and
the same wall the owner's own `keygen.py setup` hits on Windows.

Linux has no text-mode translation, so on POSIX these tests MODEL
the CRT behaviour: os.open/os.write are wrapped so descriptors
opened without O_BINARY translate 0x0A -> 0x0D 0x0A on write,
exactly as the Windows CRT does. On Windows itself no model is
needed — or possible: a descriptor the real os.open returns
without O_BINARY is already a genuine CRT text-mode descriptor, so
wrapping os.write there would translate on top of the CRT's own
translation and every 0x0A would land as 0x0D 0x0D 0x0A. That
double translation is exactly what the second app-v1.0.3 build
died on (the control below produced a\\r\\r\\nb\\r\\r\\n on the
Windows runner while passing on Linux), so on a Windows host the
fixture steps aside and lets the real CRT be the model. A control
test proves translation really happens on each host, so the
round-trip tests cannot pass vacuously. Key material is forced to
adversarial bytes (0x0A, 0x0D, 0x0D0A pairs, a trailing 0x0A) so
the round-trip is deterministic instead of a coin flip.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
KEYGEN = REPO_ROOT / "tools" / "keygen.py"

# The CRT's O_BINARY value on Windows. Linux Python has no such
# constant; the model installs it so code that asks for binary
# mode (getattr(os, "O_BINARY", 0)) behaves as it does on Windows.
_WIN_O_BINARY = 0x8000


def _load_keygen():
    spec = importlib.util.spec_from_file_location("hp_keygen", KEYGEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def keygen():
    return _load_keygen()


@contextlib.contextmanager
def windows_text_mode(monkeypatch):
    """Model the Windows CRT: an os.open without O_BINARY is a
    text-mode descriptor whose writes translate 0x0A -> 0x0D 0x0A;
    an os.open with O_BINARY is left alone. Reads are untouched —
    the model's point is the write side, matching load_keys' "rb".

    The model supplies the CRT only where the host has none. When
    os.O_BINARY already exists natively — CPython defines it only
    on Windows — the host's descriptors are real CRT descriptors
    and the real CRT performs the translation itself; installing
    the wrappers there would translate a second time (every 0x0A
    landing as 0x0D 0x0D 0x0A), so the fixture yields untouched
    and the control below exercises genuine text mode instead.
    """
    if hasattr(os, "O_BINARY"):
        yield
        return
    monkeypatch.setattr(os, "O_BINARY", _WIN_O_BINARY, raising=False)
    real_open, real_write, real_close = os.open, os.write, os.close
    text_fds = set()

    def open_wrapper(path, flags, mode=0o777, *args, **kwargs):
        fd = real_open(path, flags, mode, *args, **kwargs)
        if not (flags & os.O_BINARY):
            text_fds.add(fd)
        return fd

    def write_wrapper(fd, data):
        if fd in text_fds:
            data = bytes(data).replace(b"\n", b"\r\n")
        return real_write(fd, data)

    def close_wrapper(fd):
        text_fds.discard(fd)
        return real_close(fd)

    monkeypatch.setattr(os, "open", open_wrapper)
    monkeypatch.setattr(os, "write", write_wrapper)
    monkeypatch.setattr(os, "close", close_wrapper)
    yield


def test_windows_text_mode_model_translates_unflagged_writes(
        monkeypatch, tmp_path):
    """Control: the model must really translate, or the
    round-trip tests below prove nothing."""
    with windows_text_mode(monkeypatch):
        plain = tmp_path / "plain.bin"
        fd = os.open(str(plain),
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, b"a\nb\n")
        finally:
            os.close(fd)
        assert plain.read_bytes() == b"a\r\nb\r\n"

        binary = tmp_path / "binary.bin"
        fd = os.open(str(binary),
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY,
                     0o600)
        try:
            os.write(fd, b"a\nb\n")
        finally:
            os.close(fd)
        assert binary.read_bytes() == b"a\nb\n"


class _FakePub:
    def public_bytes_raw(self):
        return _FakePriv.material["pub"]


class _FakePriv:
    """Stands in for Ed25519PrivateKey with forced key material,
    so the bytes cmd_setup writes are the adversarial ones."""

    material = {"seed": b"", "pub": b""}

    @classmethod
    def generate(cls):
        return cls()

    def private_bytes_raw(self):
        return type(self).material["seed"]

    def public_key(self):
        return _FakePub()

    @classmethod
    def from_private_bytes(cls, seed):
        assert len(seed) == 32
        return cls()


_ADVERSARIAL = [
    # mixed: lone 0x0A, a 0x0D0A pair, 0x1A, trailing 0x0A
    (bytes([0x0A, 0x41, 0x0D, 0x0A, 0x42, 0x1A, 0x0D] + [0x61] * 24
           + [0x0A]),
     bytes([0x0A] * 4 + [0x62] * 27 + [0x0D]),
     bytes([0x63] * 31 + [0x0A])),
    # extremes: all newlines / newline-last / alternating pair
    (bytes([0x0A] * 32),
     bytes([0x0D] * 31 + [0x0A]),
     bytes([0x0A, 0x0D] * 16)),
    # natural: the byte range itself carries 0x0A and 0x0D
    (bytes(range(32)),
     bytes([0xFF] * 15 + [0x0A] + [0x00] * 16),
     bytes(32)),
]


@pytest.mark.parametrize("seed,kc,pub", _ADVERSARIAL)
def test_setup_load_roundtrip_survives_windows_text_mode(
        keygen, monkeypatch, tmp_path, seed, kc, pub):
    _FakePriv.material = {"seed": seed, "pub": pub}
    monkeypatch.setattr(keygen, "need_crypto",
                        lambda: (_FakePriv, None, None, None))
    real_urandom = os.urandom
    os.urandom = lambda n: kc[:n]
    try:
        with windows_text_mode(monkeypatch):
            keygen.cmd_setup(str(tmp_path))
            paths = keygen.key_paths(str(tmp_path))
            # The files on disk must be the exact key material —
            # no translation, no inflation, for all three files.
            assert Path(paths["priv"]).read_bytes() == seed
            assert Path(paths["kc"]).read_bytes() == kc
            assert Path(paths["pub"]).read_bytes() == pub
            _, loaded_kc = keygen.load_keys(str(tmp_path))
            assert loaded_kc == kc
    finally:
        os.urandom = real_urandom


def test_setup_load_roundtrip_real_crypto(keygen, tmp_path):
    """The plain round-trip with genuine key material (the path
    the owner's setup takes), no model involved."""
    pytest.importorskip("cryptography")
    keygen.cmd_setup(str(tmp_path))
    paths = keygen.key_paths(str(tmp_path))
    for name in ("priv", "kc", "pub"):
        assert len(Path(paths[name]).read_bytes()) == 32
    _, kc = keygen.load_keys(str(tmp_path))
    assert len(kc) == 32
