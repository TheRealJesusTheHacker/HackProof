# PyInstaller spec for HackProof.exe — the whole product in one
# file: the app, the self-install engine, and the setup/uninstall
# flows, routed at launch by hackproof_app.entry (the ARGUS.EXE
# pattern).
#
# Build (from the repo root, on Windows):
#     python app/tools/bundle_site.py        # makes app/build/webroot
#     pyinstaller app/packaging/HackProof.spec --noconfirm
# Output: dist/HackProof.exe
#
# One-file, no console window. The course website ships inside as
# data (hackproof_webroot) — bundled from the repo's site tree at
# build time, never forked into the app package. Qt WebEngine
# (the course browser) is collected by PyInstaller's PySide6
# hooks; the workflow's --self-check-qt gate constructs a real
# web view from the built exe so a build that dropped the engine
# fails in CI, not on a customer's machine.

from pathlib import Path

# PyInstaller does NOT inject the version-info classes into the
# spec namespace (the ARGUS.EXE v1.1.2 lesson): import them.
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

ROOT = Path(SPECPATH).parent.parent  # repo root
APP = ROOT / "app"
WEBROOT = APP / "build" / "webroot"

if not (WEBROOT / "app-manifest.json").is_file():
    raise SystemExit(
        "app/build/webroot is missing — run "
        "`python app/tools/bundle_site.py` first (the release "
        "workflow does this). Refusing to build a HackProof.exe "
        "without the course inside."
    )

# Windows version resource: Explorer, the task manager, and
# SmartScreen read THIS — an exe with no version info looks
# anonymous. Version 1.0.2 matches hackproof_app.__version__
# (the release workflow's tag check keeps them from drifting).
version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 2, 0),
        prodvers=(1, 0, 2, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct(
                            "CompanyName", "Sentinel Safeguard LLC"
                        ),
                        StringStruct(
                            "FileDescription",
                            "HackProof — cybersecurity course",
                        ),
                        StringStruct("FileVersion", "1.0.2.0"),
                        StringStruct("InternalName", "HackProof"),
                        StringStruct(
                            "LegalCopyright",
                            "© Sentinel Safeguard LLC",
                        ),
                        StringStruct("OriginalFilename", "HackProof.exe"),
                        StringStruct("ProductName", "HackProof"),
                        StringStruct("ProductVersion", "1.0.2"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
    ],
)

a = Analysis(
    [str(APP / "packaging" / "launch_hackproof.py")],
    pathex=[str(APP)],
    binaries=[],
    datas=[
        # The bundled course website (build-time artifact).
        (str(WEBROOT), "hackproof_webroot"),
        # App-owned assets (reader template, QR page, icon).
        (str(APP / "hackproof_app" / "gui" / "assets"),
         "hackproof_app/gui/assets"),
    ],
    hiddenimports=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtNetwork",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="HackProof",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(APP / "packaging" / "hackproof.ico"),
    version=version_info,
)
