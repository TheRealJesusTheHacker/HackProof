"""PyInstaller entry shim for HackProof.exe.

PyInstaller runs this file as a top-level script; it puts the
``app/`` folder on the path (in a source checkout) and hands over
to :func:`hackproof_app.entry.main`, which routes the launch.
In the frozen build the package is already importable — the path
insert is a harmless no-op then.
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_app_dir = os.path.dirname(_here)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from hackproof_app.entry import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
