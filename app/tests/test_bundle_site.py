"""The site bundler: exclusions (owner tooling, service, pack
SOURCES never ship), constant rewiring, pack detection, manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hackproof_app import site_bundle
from tools.bundle_site import (
    apply_brand_theme,
    build_manifest,
    copy_site,
    default_out,
    main,
    rewire_constants,
    rewrite_buy_links,
)


def test_default_out_is_the_apps_build_webroot():
    # CI runs the bundler with no --out; the spec packages exactly
    # app/build/webroot, and site_bundle finds it there in dev.
    assert default_out().parts[-3:] == ("app", "build", "webroot")

PUBKEY = "ab" * 32


def make_site(root: Path, *, pack: str = "empty") -> Path:
    (root / "course").mkdir(parents=True)
    (root / "course" / "01-welcome.md").write_text("# Welcome")
    (root / "index.html").write_text(
        "<h1>HackProof</h1><style>body{background:#0a0612;"
        "color:#efe8fa}.a{color:#a855f7;"
        "box-shadow:0 0 0 3px #a855f733}</style>"
    )
    (root / "verify.html").write_text("<h1>Verify</h1>")
    (root / "exam.html").write_text(
        '<script>const CERT_SERVICE_BASE_URL = ""; '
        'const PAYMENTS_API_BASE = ""; '
        'const CERT_SUBMIT_URL = CERT_SERVICE_BASE_URL + "/api/certificates";'
        "</script>"
        '<a href="game/buy.html">Get premium</a>'
    )
    marker = "BUILT-CIPHERTEXT" if pack == "built" else ""
    shared = (
        'const HP = { LICENSE_PUBLIC_KEY_HEX: "' + PUBKEY + '" };\n'
    )
    if pack != "absent":
        shared += (
            'const PREMIUM_PACK_B64 = /*__PREMIUM_PACK__*/ "'
            + marker + '";'
        )
    (root / "shared.js").write_text(shared)
    # Things that must NEVER ship inside the app:
    (root / "tools").mkdir()
    (root / "tools" / "keygen.py").write_text("SECRET KEY TOOL")
    (root / "payments").mkdir()
    (root / "payments" / "certsvc.py").write_text("SERVER")
    (root / "content").mkdir()
    (root / "content" / "premium-source.md").write_text("PLAINTEXT PREMIUM")
    (root / "app").mkdir()
    (root / "app" / "inner.txt").write_text("APP ITSELF")
    (root / "game").mkdir()
    (root / "game" / "buy.html").write_text("GAME BUY PAGE")
    # game/index.html IS the course catalog + reader: it ships.
    (root / "game" / "index.html").write_text(
        '<h1>Course</h1><a href="buy.html">Get premium</a>'
        '<p style="color:rgba(168,85,247,.5)">glow</p>'
    )
    return root


@pytest.fixture()
def bundled(tmp_path):
    repo = make_site(tmp_path / "repo")
    out = tmp_path / "webroot"
    out.mkdir()
    copied = copy_site(repo, out)
    rewired = rewire_constants(out)
    manifest = build_manifest(repo, out, copied, rewired)
    return repo, out, manifest


def test_exclusions(bundled):
    _, out, _ = bundled
    names = {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()}
    assert "index.html" in names and "course/01-welcome.md" in names
    assert not any(n.startswith("tools/") for n in names)
    assert not any(n.startswith("payments/") for n in names)
    assert not any(n.startswith("content/") for n in names)
    assert not any(n.startswith("app/") for n in names)
    # The course page ships; the website's buy page never does —
    # buying inside the app is the native My Premium screen.
    assert "game/index.html" in names
    assert "game/buy.html" not in names


def test_rewiring_points_exam_at_app_origin(bundled):
    _, out, manifest = bundled
    exam = (out / "exam.html").read_text()
    assert 'CERT_SERVICE_BASE_URL = "hackproof://app"' in exam
    assert "exam.html:CERT_SERVICE_BASE_URL" in manifest["rewired_constants"]
    # The exam page's real constant is an *_API_BASE one; missing
    # it leaves in-app certificate delivery on the manual route.
    assert 'PAYMENTS_API_BASE = "hackproof://app"' in exam
    assert "exam.html:PAYMENTS_API_BASE" in manifest["rewired_constants"]


def _purple_family(hex6: str) -> bool:
    """Hue/saturation test: violet hues with real saturation.
    Near-neutral lavenders (sat <= .08) read as grey/white and
    are handled by the map's text-tone entries instead."""
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn or mx == 0:
        return False
    sat = (mx - mn) / mx
    if mx == r:
        hue = (60 * ((g - b) / (mx - mn)) + 360) % 360
    elif mx == g:
        hue = 120 + 60 * ((b - r) / (mx - mn))
    else:
        hue = 240 + 60 * ((r - g) / (mx - mn))
    return 225 <= hue <= 335 and sat > 0.08


def test_no_purple_family_survives_the_brand_pass(bundled):
    import re

    _, out, _ = bundled
    apply_brand_theme(out)
    hex6 = re.compile(r"#[0-9a-fA-F]{6}(?![0-9a-fA-F])")
    offenders = []
    for path in out.rglob("*"):
        if path.suffix not in (".html", ".js", ".css"):
            continue
        for token in hex6.findall(path.read_text(errors="replace")):
            if _purple_family(token.lower()):
                offenders.append((str(path.relative_to(out)), token))
    assert not offenders, offenders


def test_buy_links_point_at_the_app(bundled):
    repo, out, _ = bundled
    touched = rewrite_buy_links(out)
    assert set(touched) == {"exam.html", "game/index.html"}
    assert 'href="/_app/buy-in-app.html"' in (out / "exam.html").read_text()
    assert 'href="/_app/buy-in-app.html"' in (
        out / "game" / "index.html"
    ).read_text()
    # The repository files are never touched.
    assert 'href="game/buy.html"' in (repo / "exam.html").read_text()
    assert 'href="buy.html"' in (repo / "game" / "index.html").read_text()


def test_brand_theme_applied_to_bundled_copies_only(bundled):
    repo, out, _ = bundled
    counts = apply_brand_theme(out)
    assert counts  # something changed
    index = (out / "index.html").read_text().lower()
    assert "#a855f7" not in index and "#0a0612" not in index
    assert "#1e7a3c" in index and "#060a07" in index
    assert "#1e7a3c33" in index  # the alpha form keeps its alpha
    course = (out / "game" / "index.html").read_text()
    assert "168,85,247" not in course
    assert "30,122,60" in course
    # Repository originals keep the website's own palette.
    assert "#a855f7" in (repo / "index.html").read_text()


def test_manifest_facts(bundled):
    _, out, manifest = bundled
    assert manifest["pages"] == {"course": True, "exam": True, "verify": True}
    assert manifest["public_key_hex"] == PUBKEY
    assert manifest["pack"]["state"] == site_bundle.PACK_NOT_BUILT
    assert manifest["modules"] == [
        {"path": "course/01-welcome.md", "kind": "markdown"}
    ]
    assert any("pack" in w for w in manifest["warnings"])


def test_pack_states(tmp_path):
    for pack, expected in (
        ("built", site_bundle.PACK_BUILT),
        ("empty", site_bundle.PACK_NOT_BUILT),
        ("absent", site_bundle.PACK_ABSENT),
    ):
        repo = make_site(tmp_path / pack, pack=pack)
        out = tmp_path / (pack + "-out")
        out.mkdir()
        manifest = build_manifest(repo, out, copy_site(repo, out), [])
        assert manifest["pack"]["state"] == expected, pack


def test_game_pack_artifact_ships_without_the_buy_page(tmp_path):
    repo = make_site(tmp_path / "repo", pack="absent")
    (repo / "game" / "premium-pack.b64").write_text("Q0lQSEVSVEVYVA==")
    out = tmp_path / "webroot"
    out.mkdir()
    copy_site(repo, out)
    assert (out / "premium-pack.b64").is_file()
    assert (out / "game" / "index.html").is_file()
    assert not (out / "game" / "buy.html").exists()
    manifest = build_manifest(repo, out, [], [])
    assert manifest["pack"]["state"] == site_bundle.PACK_BUILT


def test_main_writes_manifest(tmp_path):
    repo = make_site(tmp_path / "repo")
    out = tmp_path / "webroot"
    assert main(["--repo", str(repo), "--out", str(out)]) == 0
    manifest = json.loads((out / "app-manifest.json").read_text())
    assert manifest["public_key_hex"] == PUBKEY
    loaded = site_bundle.load_manifest(out)
    assert loaded.page_present("course")
    assert loaded.public_key_hex == PUBKEY


def test_site_bundle_webroot_env(tmp_path, monkeypatch):
    rooted = tmp_path / "wr"
    rooted.mkdir()
    (rooted / "app-manifest.json").write_text(json.dumps({
        "pages": {"course": True},
        "pack": {"state": "built", "bytes": 10},
    }))
    monkeypatch.setenv(site_bundle.WEBROOT_ENV, str(rooted))
    assert site_bundle.webroot() == rooted
    manifest = site_bundle.load_manifest()
    assert manifest.pack_state == site_bundle.PACK_BUILT
    assert manifest.page_present("course")
