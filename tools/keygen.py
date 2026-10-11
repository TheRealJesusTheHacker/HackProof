#!/usr/bin/env python3
"""
Copyright (c) 2026 JesusTheHacker. All rights reserved.
No copying, redistribution, or derivative works without written permission.

HackProof license-key + premium-pack tooling.
*** AUTHORITATIVE as of 2026-10-11 — supersedes all earlier key schemes. ***

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  PRIVATE KEY MATERIAL — NEVER COMMIT, NEVER SHARE                  !!
!!                                                                    !!
!!  `setup` writes TWO secrets to ~/.hackproof/ (chmod 600):          !!
!!    1. Ed25519 signing keypair (ed25519-private.key = 32-byte seed)  !!
!!    2. 256-bit master content key Kc (content-master.key)            !!
!!  These are the master keys to your product. Anyone holding them    !!
!!  can mint licenses and decrypt the premium pack.                   !!
!!                                                                    !!
!!  - NEVER commit them to this repo (or any repo / gist / ticket).   !!
!!  - NEVER paste them into chat, email, docs, or screenshots.        !!
!!  - Minting and pack-building happen ONLY on YOUR OWN machine.      !!
!!  - This script contains NO key material — it reads your local      !!
!!    files, uses them, and forgets them.                             !!
!!  If either secret leaks: run `setup` again (fresh keys), paste the !!
!!  NEW public key into game/index.html CONFIG, re-run `build-pack`,  !!
!!  and re-mint every customer license.                               !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

GOING LIVE (4 commands, all on your own machine):

  1. python3 tools/keygen.py setup
       -> generates keys in ~/.hackproof/, prints your PUBLIC key.

  2. Paste the printed PUBLIC key hex into game/index.html:
       CONFIG.LICENSE_PUBLIC_KEY_HEX = "<paste here>"
     (replacing the REPLACE_ME placeholder), then commit + deploy.

  3. python3 tools/keygen.py build-pack
       -> encrypts content/premium/ (5 scenarios + 16 modules) with Kc,
          writes game/premium-pack.b64 and inlines the ciphertext into
          game/index.html. Commit + deploy the result.

  4. python3 tools/keygen.py mint --tier premium --days 365
       -> prints a license key. Email it to the paying customer.
          They paste it into the game's "Enter license key" box.

Requires: pip install cryptography

SCHEME (so you can audit it):
  License = base64( JSON {id, tier:"premium", expiry, S, wrapped_Kc, sig} )
    S          = fresh 256-bit random per license (base64)
    wrapped_Kc = base64( iv_w || AES-256-GCM(Kw, iv_w, Kc) )
    Kw         = HKDF-SHA256(S, salt="", info="hackproof-wrap", 32 bytes)
    sig        = Ed25519(priv, canonical JSON of {id,tier,expiry,S,wrapped_Kc})
  Pack = base64( iv_p || AES-256-GCM(Kc, iv_p, utf8(pack_json)) )
    pack_json  = {"scenarios":[...5...], "modules":[...16...]}
  The game verifies sig with the embedded public key (tweetnacl),
  checks tier+expiry, unwraps Kc via WebCrypto, and decrypts the pack.
  Without a valid license the pack is random bytes. License-sharing
  between users is out of scope — no client-side scheme stops that.
"""

import argparse
import base64
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_KEYDIR = os.path.expanduser("~/.hackproof")
WRAP_INFO = b"hackproof-wrap"


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def need_crypto():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        return Ed25519PrivateKey, AESGCM, HKDF, hashes
    except ImportError:
        sys.exit("The 'cryptography' package is required: pip install cryptography")


def key_paths(keydir):
    return {
        "priv": os.path.join(keydir, "ed25519-private.key"),
        "pub": os.path.join(keydir, "ed25519-public.key"),
        "kc": os.path.join(keydir, "content-master.key"),
    }


def cmd_setup(keydir):
    Ed25519PrivateKey, _, _, _ = need_crypto()
    os.makedirs(keydir, exist_ok=True)
    os.chmod(keydir, 0o700)
    paths = key_paths(keydir)
    for p in paths.values():
        if os.path.exists(p):
            sys.exit("REFUSING: %s already exists. Delete it by hand if you "
                     "really want to rotate keys." % p)
    priv = Ed25519PrivateKey.generate()
    try:
        seed = priv.private_bytes_raw()
        pub = priv.public_key().public_bytes_raw()
    except AttributeError:
        from cryptography.hazmat.primitives import serialization
        seed = priv.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption())
        pub = priv.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw)
    kc = os.urandom(32)
    with open(paths["priv"], "wb") as f:
        f.write(seed)
    with open(paths["pub"], "wb") as f:
        f.write(pub)
    with open(paths["kc"], "wb") as f:
        f.write(kc)
    for p in (paths["priv"], paths["kc"]):
        os.chmod(p, 0o600)
    os.chmod(paths["pub"], 0o644)
    print("Wrote key material to %s (chmod 600 on secrets)" % keydir)
    print("  ed25519-private.key  <- NEVER commit, NEVER share")
    print("  content-master.key   <- NEVER commit, NEVER share")
    print("  ed25519-public.key    <- this one is public")
    print()
    print("STEP 2 — paste this PUBLIC key into game/index.html:")
    print("  CONFIG.LICENSE_PUBLIC_KEY_HEX = \"%s\"" % pub.hex())


def load_keys(keydir):
    Ed25519PrivateKey, _, _, _ = need_crypto()
    paths = key_paths(keydir)
    for name, p in paths.items():
        if not os.path.exists(p):
            sys.exit("Missing %s — run `setup` first." % p)
    with open(paths["priv"], "rb") as f:
        seed = f.read()
    with open(paths["kc"], "rb") as f:
        kc = f.read()
    if len(seed) != 32 or len(kc) != 32:
        sys.exit("Key files look corrupt (expected 32 bytes each).")
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    return priv, kc


def canonical_fields(lic):
    # Fixed key order — the game rebuilds this exact string to verify.
    return json.dumps(
        {"id": lic["id"], "tier": lic["tier"], "expiry": lic["expiry"],
         "S": lic["S"], "wrapped_Kc": lic["wrapped_Kc"]},
        separators=(",", ":"))


def cmd_mint(keydir, tier, days):
    import time
    _, AESGCM, HKDF, hashes = need_crypto()
    if tier not in ("premium",):
        sys.exit("tier must be 'premium' (free needs no license)")
    priv, kc = load_keys(keydir)
    S = os.urandom(32)
    kw = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"",
              info=WRAP_INFO).derive(S)
    iv_w = os.urandom(12)
    wrapped = iv_w + AESGCM(kw).encrypt(iv_w, kc, None)
    lic = {
        "id": b64e(os.urandom(6)),
        "tier": tier,
        "expiry": int(time.time()) + days * 86400,
        "S": b64e(S),
        "wrapped_Kc": b64e(wrapped),
    }
    sig = priv.sign(canonical_fields(lic).encode("utf-8"))
    lic["sig"] = b64e(sig)
    license_key = b64e(json.dumps(lic, separators=(",", ":")).encode("utf-8"))
    print("LICENSE KEY (%s, %d days) — email this to the customer:" % (tier, days))
    print(license_key)
    print()
    print("key id: %s  expires: %s" %
          (lic["id"], time.strftime("%Y-%m-%d", time.gmtime(lic["expiry"]))))


def cmd_build_pack(keydir, content_dir, game_dir):
    _, AESGCM, _, _ = need_crypto()
    _, kc = load_keys(keydir)
    scen_dir = os.path.join(content_dir, "scenarios")
    mod_dir = os.path.join(content_dir, "modules")
    if not os.path.isdir(scen_dir) or not os.path.isdir(mod_dir):
        sys.exit("Expected %s and %s" % (scen_dir, mod_dir))
    scenarios = []
    for fn in sorted(os.listdir(scen_dir)):
        if fn.endswith(".json"):
            with open(os.path.join(scen_dir, fn), encoding="utf-8") as f:
                scenarios.append(json.load(f))
    modules = []
    for fn in sorted(os.listdir(mod_dir)):
        if fn.endswith(".md"):
            with open(os.path.join(mod_dir, fn), encoding="utf-8") as f:
                modules.append({"file": fn, "body": f.read()})
    if len(scenarios) != 5:
        sys.exit("Expected 5 premium scenario JSONs, found %d" % len(scenarios))
    if len(modules) != 16:
        sys.exit("Expected 16 premium module .md files, found %d" % len(modules))
    pack = {"scenarios": scenarios, "modules": modules}
    plaintext = json.dumps(pack, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    iv_p = os.urandom(12)
    blob = b64e(iv_p + AESGCM(kc).encrypt(iv_p, plaintext, None))
    # 1) canonical artifact on disk
    b64_path = os.path.join(game_dir, "premium-pack.b64")
    with open(b64_path, "w", encoding="utf-8") as f:
        f.write(blob + "\n")
    # 2) inline into game/index.html so premium works from file:// too
    html_path = os.path.join(game_dir, "index.html")
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    marker = "/*__PREMIUM_PACK__*/"
    if marker not in html:
        sys.exit("Marker %s not found in %s" % (marker, html_path))
    # Replace the whole marked line:  /*__PREMIUM_PACK__*/ ""
    import re
    html2, n = re.subn(
        r"/\*__PREMIUM_PACK__\*/\s*\"[^\"]*\"",
        marker + ' "' + blob + '"',
        html, count=1)
    if n != 1:
        sys.exit("Could not replace the premium-pack placeholder line.")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html2)
    print("Pack built: %d scenarios, %d modules, %d plaintext bytes" %
          (len(scenarios), len(modules), len(plaintext)))
    print("  wrote %s" % b64_path)
    print("  inlined ciphertext into %s" % html_path)
    print("Commit + deploy both.")


def main():
    ap = argparse.ArgumentParser(description="HackProof license + pack tooling")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup", help="generate signing keypair + content key")
    s.add_argument("--keydir", default=DEFAULT_KEYDIR)
    m = sub.add_parser("mint", help="mint a license key")
    m.add_argument("--keydir", default=DEFAULT_KEYDIR)
    m.add_argument("--tier", default="premium")
    m.add_argument("--days", type=int, default=365)
    b = sub.add_parser("build-pack", help="encrypt content/premium into the pack")
    b.add_argument("--keydir", default=DEFAULT_KEYDIR)
    b.add_argument("--content", default=os.path.join(REPO_ROOT, "content", "premium"))
    b.add_argument("--game", default=os.path.join(REPO_ROOT, "game"))
    args = ap.parse_args()
    if args.cmd == "setup":
        cmd_setup(args.keydir)
    elif args.cmd == "mint":
        cmd_mint(args.keydir, args.tier, args.days)
    elif args.cmd == "build-pack":
        cmd_build_pack(args.keydir, args.content, args.game)


if __name__ == "__main__":
    main()
