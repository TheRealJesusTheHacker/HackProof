#!/usr/bin/env python3
"""Generate the HackProof icon (PNG asset + Windows .ico).

Design: the watcher motif in the academy colors — an emerald
ring (the eye that checks everything) around a solid pupil, on
the ink-black rounded square (hackproof_app.gui.theme: BG,
PANEL_BORDER, PRIMARY). Drawn with QPainter so the shapes are
vector-clean at every size; the .ico embeds PNG frames (the
format Windows accepts for 256px icons).

Run (needs PySide6, offscreen is fine):
    python app/tools/make_icon.py
Outputs:
    app/hackproof_app/gui/assets/hackproof.png   (256px window icon)
    app/packaging/hackproof.ico                  (installer/exe icon)
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_png(size: int) -> bytes:
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF
    from PySide6.QtGui import QColor, QImage, QPainter, QPen

    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = float(size)
    # Rounded square in green-black.
    painter.setBrush(QColor("#050807"))
    painter.setPen(QPen(QColor("#1e2b21"), max(1.0, s * 0.012)))
    radius = s * 0.20
    painter.drawRoundedRect(
        QRectF(s * 0.03, s * 0.03, s * 0.94, s * 0.94), radius, radius
    )
    # The eye: green ring + solid pupil.
    painter.setBrush(QColor(0, 0, 0, 0))
    painter.setPen(QPen(QColor("#1da463"), s * 0.075))
    painter.drawEllipse(QRectF(s * 0.24, s * 0.24, s * 0.52, s * 0.52))
    painter.setBrush(QColor("#1da463"))
    painter.setPen(QPen(QColor("#1da463"), 1))
    painter.drawEllipse(QRectF(s * 0.415, s * 0.415, s * 0.17, s * 0.17))
    painter.end()
    array = QByteArray()
    buffer = QBuffer(array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(array)


def build_ico(frames: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(frames))
    entries = b""
    offset = 6 + 16 * len(frames)
    blobs = b""
    for size, png in frames:
        dim = 0 if size >= 256 else size
        entries += struct.pack(
            "<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset
        )
        blobs += png
        offset += len(png)
    return header + entries + blobs


def main() -> int:
    here = Path(__file__).resolve()
    assets = here.parent.parent / "hackproof_app" / "gui" / "assets"
    packaging = here.parent.parent / "packaging"
    frames = [(size, render_png(size)) for size in SIZES]
    png256 = dict(frames)[256]
    (assets / "hackproof.png").write_bytes(png256)
    (packaging / "hackproof.ico").write_bytes(build_ico(frames))
    print(f"wrote {assets / 'hackproof.png'} ({len(png256)} bytes)")
    ico = packaging / "hackproof.ico"
    print(f"wrote {ico} ({ico.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
