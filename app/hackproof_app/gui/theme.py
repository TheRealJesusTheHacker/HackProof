"""The HackProof theme: the academy's emerald and gold on ink-black.

One theme for every window the product shows — the main window,
the setup and uninstall flows, dialogs. HackProof is Sentinel's
academy, its proving ground, and since app-v1.0.4 it wears its
own colors: an ink-black base, a deep academy emerald evolved
away from the house Sentinel green (the two greens are never
interchangeable — this one is the academy's), and certificate
gold as the accent, the color of the seal on the certificate the
course exists to earn.

The palette below is the single source of truth. The locked
constants are the design set; the remaining tones are DERIVED
from them by the documented mixes (channel-wise in sRGB, the
fleet's derivation convention) and pinned by the theme tests, so
they cannot drift. Every text/background pair the stylesheet
renders meets WCAG AA (≥ 4.5:1); the weakest is the design
pair, DISABLED_TEXT on PANEL at 5.17:1. The danger tones are
the app's long-standing functional reds — pale red text on a
dark red ground, 11.8:1 / 9.6:1 — retained exactly: they are
not identity colors and they already pass with room. There is
NO light background and NO purple anywhere in the app chrome —
the course pages render in the same academy palette inside the
browser view (the bundler's BRAND_MAP carries these constants
into the bundled copies; the website keeps its own design).

``apply_theme(app)`` is the single entry point: Fusion style (so
the palette is honored exactly), the dark QPalette, and the QSS
that styles the widgets Fusion leaves plain.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

# ----------------------------------------------------------------------
# The academy palette (locked design constants)
# ----------------------------------------------------------------------
BG = "#050807"                  # ink-black app background
PANEL = "#0a100c"               # cards / panels
PANEL_BORDER = "#1e2b21"        # hairline borders
INPUT_BG = "#080d09"            # input surfaces

TEXT = "#e9f2ea"                # primary text
TEXT_FAINT = "#90a894"          # secondary text
DISABLED_TEXT = "#77897b"       # tertiary / disabled text

PRIMARY = "#1da463"             # academy emerald — primary accent
PRIMARY_DARK_TEXT = "#02120a"   # near-black text on PRIMARY fills
ACCENT = "#c9a227"              # certificate gold — attention accent

# ----------------------------------------------------------------------
# Derived tones. Each is a channel-wise sRGB mix of locked
# constants, stated as (base, toward, fraction of the second):
# the theme tests recompute every one from the constants above.
# ----------------------------------------------------------------------
PANEL_RAISED = "#171e19"        # PANEL 94% + TEXT 6% — raised surfaces
HOVER = "#182b20"               # PANEL_RAISED 90% + PRIMARY 10%
PRIMARY_HOVER = "#42b27b"       # PRIMARY 82% + TEXT 18%
DEEP = "#115635"                # PRIMARY 50% + BG 50% — selections,
                                # pressed fills, progress, cert accents
DIM = "#8dcfad"                 # PRIMARY 45% + TEXT 55% — pale emerald
                                # secondary text (monospace labels)
DISABLED_FILL = "#0b2f1e"       # PRIMARY 25% + BG 75% — the disabled
                                # primary button's fill
OUTLINE = "#515d53"             # PANEL_BORDER 75% + TEXT 25% — the
                                # checkbox outline, visible on PANEL

SELECTION_TEXT = "#ffffff"      # on DEEP

# Danger: the app's functional reds, retained exactly (see the
# module docstring). Pale text on dark grounds — never a fill
# behind small text at low contrast.
DANGER_BG = "#3d1113"
DANGER_BORDER = "#6e1d20"
DANGER_TEXT = "#ffb3b3"

# Working-name aliases for the roles the app already used; they
# are the same values, bound to the constants above.
BORDER = PANEL_BORDER
GREEN = PRIMARY
GREEN_HOVER = PRIMARY_HOVER
GREEN_DEEP = DEEP
GREEN_DIM = DIM
TEXT_DIM = TEXT_FAINT
PRIMARY_TEXT = PRIMARY_DARK_TEXT
GOLD = ACCENT


def _palette() -> QPalette:
    palette = QPalette()
    role = QPalette.ColorRole
    group = QPalette.ColorGroup
    palette.setColor(role.Window, QColor(BG))
    palette.setColor(role.WindowText, QColor(TEXT))
    palette.setColor(role.Base, QColor(INPUT_BG))
    palette.setColor(role.AlternateBase, QColor(PANEL_RAISED))
    palette.setColor(role.Text, QColor(TEXT))
    palette.setColor(role.BrightText, QColor(PRIMARY))
    palette.setColor(role.Button, QColor(PANEL_RAISED))
    palette.setColor(role.ButtonText, QColor(TEXT))
    palette.setColor(role.Highlight, QColor(DEEP))
    palette.setColor(role.HighlightedText, QColor(SELECTION_TEXT))
    palette.setColor(role.Link, QColor(PRIMARY))
    palette.setColor(role.ToolTipBase, QColor(PANEL_RAISED))
    palette.setColor(role.ToolTipText, QColor(TEXT))
    palette.setColor(role.PlaceholderText, QColor(DISABLED_TEXT))
    palette.setColor(group.Disabled, role.Text, QColor(DISABLED_TEXT))
    palette.setColor(group.Disabled, role.ButtonText, QColor(DISABLED_TEXT))
    palette.setColor(group.Disabled, role.WindowText, QColor(DISABLED_TEXT))
    return palette


QSS = """
* { font-family: "Segoe UI", "Inter", sans-serif; font-size: 14px; }
QMainWindow, QDialog { background: #050807; }
QWidget { background: #050807; color: #e9f2ea; }
QLabel { background: transparent; }
QLabel#Headline { font-size: 22px; font-weight: 700; color: #e9f2ea; }
QLabel#Subhead { font-size: 14px; color: #90a894; }
QLabel#Dim { color: #77897b; font-size: 12px; }
QLabel#Good { color: #1da463; font-weight: 600; }
QLabel#Bad { color: #ffb3b3; font-weight: 600; }
QLabel#Warn { color: #c9a227; font-weight: 600; }
QLabel#Mono { font-family: "Cascadia Mono", "Consolas", monospace;
              font-size: 13px; color: #8dcfad; }
QFrame#Card { background: #0a100c; border: 1px solid #1e2b21;
              border-radius: 10px; }
QScrollArea { background: #050807; border: none; }
QScrollBar:vertical { background: #0a100c; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #1e2b21; border-radius: 5px;
                              min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #115635; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0; background: none; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; }
QFrame#Banner { background: #171e19; border: 1px solid #115635;
                border-radius: 10px; }
QPushButton { background: #171e19; border: 1px solid #1e2b21;
              border-radius: 8px; padding: 9px 16px; color: #e9f2ea; }
QPushButton:hover { background: #182b20; border-color: #1da463; }
QPushButton:pressed { background: #115635; }
QPushButton:disabled { color: #77897b; border-color: #1e2b21; }
QPushButton#Primary { background: #1da463; color: #02120a;
                      border: 1px solid #1da463; font-weight: 700; }
QPushButton#Primary:hover { background: #42b27b; }
QPushButton#Primary:disabled { background: #0b2f1e; color: #90a894;
                               border-color: #0b2f1e; }
QPushButton#Danger { background: #3d1113; border-color: #6e1d20;
                     color: #ffb3b3; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #080d09; border: 1px solid #1e2b21; border-radius: 8px;
    padding: 8px 10px; color: #e9f2ea;
    selection-background-color: #115635; selection-color: #ffffff; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #1da463; }
QListWidget#Nav { background: #0a100c; border: none;
                  border-right: 1px solid #1e2b21; outline: 0; }
QListWidget#Nav::item { padding: 13px 16px; color: #90a894;
                        border-left: 3px solid transparent; }
QListWidget#Nav::item:selected { background: #171e19; color: #e9f2ea;
                                 border-left: 3px solid #1da463; }
QListWidget#Nav::item:hover { color: #e9f2ea; }
QListWidget#Nav::item:disabled { color: #77897b; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #515d53; background: #0a100c; }
QCheckBox::indicator:checked { background: #1da463;
    border-color: #1da463; }
QProgressBar { background: #0a100c; border: 1px solid #1e2b21;
    border-radius: 6px; text-align: center; color: #e9f2ea;
    height: 18px; }
QProgressBar::chunk { background: #115635; border-radius: 5px; }
QScrollBar:vertical { background: #050807; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: #1e2b21; border-radius: 6px;
    min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #1da463; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0; background: none; }
QScrollBar:horizontal { background: #050807; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: #1e2b21; border-radius: 6px;
    min-width: 32px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0; background: none; }
QToolTip { background: #171e19; color: #e9f2ea; border: 1px solid #1e2b21;
           padding: 6px 8px; }
QMessageBox { background: #050807; }
"""


def apply_theme(app: QApplication) -> None:
    """Apply the HackProof theme to *app* (idempotent)."""
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
    app.setPalette(_palette())
    app.setStyleSheet(QSS)
