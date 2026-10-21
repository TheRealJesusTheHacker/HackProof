"""HackProof — the Sentinel Safeguard cybersecurity course, as an app.

One package, one executable (see :mod:`hackproof_app.entry`): the
course window, the self-install engine, and the setup/uninstall
flows all live here, mirroring the ARGUS.EXE single-file pattern.

The course content itself is NOT in this package — it is the
HackProof website's pages and lessons, pulled from this repository
at build time by ``app/tools/bundle_site.py`` and served to the
embedded browser by :mod:`hackproof_app.gui.webview`. This package
is the shell: premium chrome, native buy/license screens, the
payments-service client, and the installer.
"""

__version__ = "1.0.5"

#: Product identity, shared by the GUI, the installer, and the
#: Windows version resource (the release workflow keeps the spec's
#: copy honest against this one).
PRODUCT_NAME = "HackProof"
DISPLAY_NAME = "HackProof — Sentinel Safeguard"
PUBLISHER = "Sentinel Safeguard LLC"
