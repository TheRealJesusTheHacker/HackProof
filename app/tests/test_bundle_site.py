"""The site bundler: exclusions (owner tooling, service, pack
SOURCES never ship), constant rewiring, pack detection, manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hackproof_app import site_bundle
from tools.bundle_site import (
    build_manifest,
    copy_site,
    default_out,
    main,
    rewire_constants,
)


def test_default_out_is_the_apps_build_webroot():
    # CI runs the bundler with no --out; the spec packages exactly
    # app/build/webroot, and site_bundle finds it there in dev.
    assert default_out().parts[-3:] == ("app", "build", "webroot")

PUBKEY = "ab" * 32


def make_site(root: Path, *, pack: str = "empty") -> Path:
    (root / "course").mkdir(parents=True)
    (root / "course" / "01-welcome.md").write_text("# Welcome")
    (root / "index.html").write_text("<h1>HackProof</h1>")
    (root / "verify.html").write_text("<h1>Verify</h1>")
    (root / "exam.html").write_text(
        '<script>const CERT_SERVICE_BASE_URL = ""; '
        'const CERT_SUBMIT_URL = CERT_SERVICE_BASE_URL + "/api/certificates";'
        "</script>"
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
    (root / "game" / "buy.html").write_text("GAME PAGE")
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
    assert not any(n.startswith("game/") for n in names)


def test_rewiring_points_exam_at_app_origin(bundled):
    _, out, manifest = bundled
    exam = (out / "exam.html").read_text()
    assert 'CERT_SERVICE_BASE_URL = "hackproof://app"' in exam
    assert "exam.html:CERT_SERVICE_BASE_URL" in manifest["rewired_constants"]


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


def test_game_pack_artifact_ships_without_game_pages(tmp_path):
    repo = make_site(tmp_path / "repo", pack="absent")
    (repo / "game" / "premium-pack.b64").write_text("Q0lQSEVSVEVYVA==")
    out = tmp_path / "webroot"
    out.mkdir()
    copy_site(repo, out)
    assert (out / "premium-pack.b64").is_file()
    assert not (out / "game").exists()
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
