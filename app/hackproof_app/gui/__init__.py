"""The HackProof desktop interface (PySide6).

Modules import PySide6 at their top; anything that must stay
importable without Qt (routing, the self-check census) lives in
:mod:`hackproof_app.entry` and imports this package lazily.
"""
