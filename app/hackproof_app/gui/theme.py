"""The HackProof theme: Sentinel green on black, everywhere.

One theme for every window the product shows — the main window,
the setup and uninstall flows, dialogs. The palette is the
Sentinel Safeguard standard (shared with ARGUS.EXE, whose contrast
ratios were measured when its theme was built: every text/background
pair below meets WCAG AA, most far beyond). There is NO light
background and NO purple anywhere in the app chrome — the course
pages render in their own design inside the browser view; the
frame around them is always this one.

``apply_theme(app)`` is the single entry point: Fusion style (so
the palette is honored exactly), the dark QPalette, and the QSS
that styles the widgets Fusion leaves plain.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

# ----------------------------------------------------------------------
# Palette (contrast ratios measured against these surfaces; see the
# Argus theme this is shared with — every pair is ≥ 4.5:1 for text)
# ----------------------------------------------------------------------
BG = "#060a07"             # app background — green-black
PANEL = "#0c130d"          # cards / panels
PANEL_RAISED = "#111a12"   # raised surfaces, buttons, hover
BORDER = "#1e3323"         # hairline borders

GREEN = "#2ee06f"          # Sentinel green — primary accent
GREEN_HOVER = "#4be884"    # primary-button hover fill
GREEN_DEEP = "#14532d"     # deep green fills (selections, pressed)
GREEN_DIM = "#8fd6a4"      # secondary green text on dark

TEXT = "#e8f2ea"           # primary text
TEXT_DIM = "#9db3a4"       # secondary text
TEXT_FAINT = "#7d927f"     # tertiary / disabled text

PRIMARY_TEXT = "#04160a"   # near-black text on GREEN fills
SELECTION_TEXT = "#ffffff"  # on GREEN_DEEP

DANGER_BG = "#3d1113"
DANGER_BORDER = "#6e1d20"
DANGER_TEXT = "#ffb3b3"

GOLD = "#ffd23d"           # attention (rare accent)


def _palette() -> QPalette:
    palette = QPalette()
    role = QPalette.ColorRole
    group = QPalette.ColorGroup
    palette.setColor(role.Window, QColor(BG))
    palette.setColor(role.WindowText, QColor(TEXT))
    palette.setColor(role.Base, QColor(PANEL))
    palette.setColor(role.AlternateBase, QColor(PANEL_RAISED))
    palette.setColor(role.Text, QColor(TEXT))
    palette.setColor(role.BrightText, QColor(GREEN))
    palette.setColor(role.Button, QColor(PANEL_RAISED))
    palette.setColor(role.ButtonText, QColor(TEXT))
    palette.setColor(role.Highlight, QColor(GREEN_DEEP))
    palette.setColor(role.HighlightedText, QColor(SELECTION_TEXT))
    palette.setColor(role.Link, QColor(GREEN))
    palette.setColor(role.ToolTipBase, QColor(PANEL_RAISED))
    palette.setColor(role.ToolTipText, QColor(TEXT))
    palette.setColor(role.PlaceholderText, QColor(TEXT_FAINT))
    palette.setColor(group.Disabled, role.Text, QColor(TEXT_FAINT))
    palette.setColor(group.Disabled, role.ButtonText, QColor(TEXT_FAINT))
    palette.setColor(group.Disabled, role.WindowText, QColor(TEXT_FAINT))
    return palette


QSS = """
* { font-family: "Segoe UI", "Inter", sans-serif; font-size: 14px; }
QMainWindow, QDialog { background: #060a07; }
QWidget { background: #060a07; color: #e8f2ea; }
QLabel { background: transparent; }
QLabel#Headline { font-size: 22px; font-weight: 700; color: #e8f2ea; }
QLabel#Subhead { font-size: 14px; color: #9db3a4; }
QLabel#Dim { color: #7d927f; font-size: 12px; }
QLabel#Good { color: #2ee06f; font-weight: 600; }
QLabel#Bad { color: #ffb3b3; font-weight: 600; }
QLabel#Warn { color: #ffd23d; font-weight: 600; }
QLabel#Mono { font-family: "Cascadia Mono", "Consolas", monospace;
              font-size: 13px; color: #8fd6a4; }
QFrame#Card { background: #0c130d; border: 1px solid #1e3323;
              border-radius: 10px; }
QFrame#Banner { background: #111a12; border: 1px solid #14532d;
                border-radius: 10px; }
QPushButton { background: #111a12; border: 1px solid #1e3323;
              border-radius: 8px; padding: 9px 16px; color: #e8f2ea; }
QPushButton:hover { background: #16251a; border-color: #2ee06f; }
QPushButton:pressed { background: #14532d; }
QPushButton:disabled { color: #7d927f; border-color: #1e3323; }
QPushButton#Primary { background: #2ee06f; color: #04160a;
                      border: 1px solid #2ee06f; font-weight: 700; }
QPushButton#Primary:hover { background: #4be884; }
QPushButton#Primary:disabled { background: #17301f; color: #9db3a4;
                               border-color: #17301f; }
QPushButton#Danger { background: #3d1113; border-color: #6e1d20;
                     color: #ffb3b3; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #0c130d; border: 1px solid #1e3323; border-radius: 8px;
    padding: 8px 10px; color: #e8f2ea;
    selection-background-color: #14532d; selection-color: #ffffff; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #2ee06f; }
QListWidget#Nav { background: #0c130d; border: none;
                  border-right: 1px solid #1e3323; outline: 0; }
QListWidget#Nav::item { padding: 13px 16px; color: #9db3a4;
                        border-left: 3px solid transparent; }
QListWidget#Nav::item:selected { background: #111a12; color: #e8f2ea;
                                 border-left: 3px solid #2ee06f; }
QListWidget#Nav::item:hover { color: #e8f2ea; }
QListWidget#Nav::item:disabled { color: #43543f; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #54855f; background: #0c130d; }
QCheckBox::indicator:checked { background: #2ee06f;
    border-color: #2ee06f; }
QProgressBar { background: #0c130d; border: 1px solid #1e3323;
    border-radius: 6px; text-align: center; color: #e8f2ea;
    height: 18px; }
QProgressBar::chunk { background: #14532d; border-radius: 5px; }
QScrollBar:vertical { background: #060a07; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #1e3323; border-radius: 6px;
    min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #2ee06f; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0; background: none; }
QScrollBar:horizontal { background: #060a07; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #1e3323; border-radius: 6px;
    min-width: 32px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0; background: none; }
QToolTip { background: #111a12; color: #e8f2ea; border: 1px solid #1e3323;
           padding: 6px 8px; }
QMessageBox { background: #060a07; }
"""


def apply_theme(app: QApplication) -> None:
    """Apply the HackProof theme to *app* (idempotent)."""
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    app.setPalette(_palette())
    app.setStyleSheet(QSS)
