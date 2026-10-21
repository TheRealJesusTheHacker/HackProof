"""The exam page's license storage honors PRIVACY.md (sweep #3).

PRIVACY.md promises the license key is kept only in the browser's
memory unless the student explicitly checks "Remember on this
device". The course page always honored that; the exam page used
to write the key (and the student's name) to localStorage
unconditionally on Begin. The fix mirrors the course page's own
opt-in — same checkbox, wording, and semantics — and keeps the
verified key in page memory so certificate delivery and the
copy-my-key button work for session-only students too.

Two pins:
- a BEHAVIORAL run of the page's real code under Node (stub DOM,
  recording localStorage): no storage write without opt-in,
  storage works with opt-in, unchecking a previously remembered
  key removes it, and a storage-denying browser still gets a
  working gate;
- BUNDLER PARITY on the real tree: the app's bundled copy of
  exam.html (the only exam the app ships) carries the fixed gate
  after the bundler's rewire + brand retint, and bundling leaves
  the repository's website file byte-identical.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).resolve().parent / "exam_storage_harness.js"


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="node is required for the exam-page harness")
def test_exam_license_storage_opt_in_behavior():
    proc = subprocess.run(
        ["node", str(HARNESS)],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "all scenarios pass" in proc.stdout


def test_bundled_exam_inherits_the_opt_in(tmp_path):
    from tools.bundle_site import (
        apply_brand_theme,
        copy_site,
        rewire_constants,
    )

    exam = REPO_ROOT / "exam.html"
    before = hashlib.sha256(exam.read_bytes()).hexdigest()
    out = tmp_path / "webroot"
    out.mkdir()
    copy_site(REPO_ROOT, out)
    rewire_constants(out)
    apply_brand_theme(out)
    bundled = (out / "exam.html").read_text(encoding="utf-8")
    # The fixed gate survives bundling (retint rewrites design
    # tokens only; the storage logic is page behavior).
    assert 'id="gate-remember"' in bundled
    assert "Remember on this device" in bundled
    assert "state.licStr" in bundled
    # The repository's website file is untouched by bundling.
    after = hashlib.sha256(exam.read_bytes()).hexdigest()
    assert before == after
