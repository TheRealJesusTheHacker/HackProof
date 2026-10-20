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
!!  The promo/test code (step 6) is BUILT INTO this tooling in       !!
!!  concealed (sealed) form — it exists nowhere in plaintext, and     !!
!!  this file NEVER ships: the app bundler excludes tools/ entirely.  !!
!!  These are the master keys to your product. Anyone holding them    !!
!!  can mint licenses and decrypt the premium pack.                   !!
!!                                                                    !!
!!  - NEVER commit them to this repo (or any repo / gist / ticket).   !!
!!  - NEVER paste them into chat, email, docs, or screenshots.        !!
!!  - Minting and pack-building happen ONLY on YOUR OWN machine.      !!
!!  - This script contains NO key material — it reads your local      !!
!!    files, uses them, and forgets them.                             !!
!!  If either secret leaks: run `setup` again (fresh keys), paste the !!
!!  NEW public key into game/index.html CONFIG and shared.js,         !!
!!  re-run `build-pack`, and re-mint every customer license.          !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

GOING LIVE (4 commands, all on your own machine):

  1. python3 tools/keygen.py setup
       -> generates keys in ~/.hackproof/, prints your PUBLIC key.

  2. Paste the printed PUBLIC key hex into BOTH files
     (replacing the REPLACE_WITH_YOUR_PUBLIC_KEY_HEX placeholder),
     then commit + deploy:
       game/index.html
       shared.js          (loaded by exam.html and verify.html)
       CONFIG.LICENSE_PUBLIC_KEY_HEX = "<paste here>"

  3. python3 tools/keygen.py build-pack
       -> encrypts content/premium/modules/ (43 course modules — the
          pack is course-only since the game was removed in Oct 2026)
          with Kc, writes game/premium-pack.b64 and inlines the
          ciphertext into game/index.html. Commit + deploy the result.

  4. python3 tools/keygen.py mint --tier premium --days 365
       -> prints a license key. Email it to the paying customer.
          They paste it into the course app's "Enter license key" box.

  5. When a student passes the final exam and emails you their
     certificate code AND their premium license key:
       python3 tools/keygen.py sign-cert --license <key> <code>
       (either value can be piped through stdin instead, with - :
        python3 tools/keygen.py sign-cert --license <key> - < code.txt)
     -> verifies the code's HMAC proof (bound to the license secret),
        checks the payload names that same license, and checks the
        score is a pass the exam page could actually have issued
        (72-90 of 90, pct exactly matching the score), then prints the
        COUNTERSIGNED code. Email it back; they paste it into
        exam.html to earn the verified seal. Anyone can check it
        at verify.html. Hand-crafted codes (missing/bad proof,
        failing/impossible/inconsistent scores) are REFUSED —
        no signature is issued.

  6. PROMO / TEST CODE — built in, nothing to set. A short numeric
     code is sealed into this tooling (see _PROMO_SEALED below: the
     digits exist in this file ONLY as an AES-256-GCM ciphertext —
     never in plaintext, in this repo or anywhere else). Every
     `build-pack` (step 3) derives the promo license from it and
     writes the promo metadata to app/promo-meta.json, which the
     app bundler ships inside the app (the website is NOT part of
     this feature — the promo lives in the app only). There is NO
     config step and NO separate mint step. Students enter the
     code in the app; it unlocks the same premium, and a
     certificate earned under it countersigns exactly like a
     purchased license's (it IS a license — see SCHEME).
     Rotate the code: replace the sealed built-in (new sealed
     blob for the new digits), re-run `build-pack`, ship the new
     app edition. Retire it for good: delete the sealed built-in,
     re-run `build-pack`, ship. The old code dies the moment the
     rebuilt edition ships.

Requires: pip install cryptography

SCHEME (so you can audit it):
  License = base64( JSON {id, tier:"premium", expiry, S, wrapped_Kc, sig} )
    S          = fresh 256-bit random per license (base64)
    wrapped_Kc = base64( iv_w || AES-256-GCM(Kw, iv_w, Kc) )
    Kw         = HKDF-SHA256(S, salt="", info="hackproof-wrap", 32 bytes)
    sig        = Ed25519(priv, canonical JSON of {id,tier,expiry,S,wrapped_Kc})
  Pack = base64( iv_p || AES-256-GCM(Kc, iv_p, utf8(pack_json)) )
    pack_json  = {"modules":[...43 course module bodies...]}
  The course app verifies sig with the embedded public key (tweetnacl),
  checks tier+expiry, unwraps Kc via WebCrypto, and decrypts the pack.
  Without a valid license the pack is random bytes. License-sharing
  between users is out of scope — no client-side scheme stops that.

  Promo = a real license whose secret is derived, not random:
    S_promo    = PBKDF2-HMAC-SHA256(code, salt, 600k iterations)
    salt       = fresh 128-bit random per pack build
    metadata   = {v, kdf, iterations, salt, {id,tier,expiry,wrapped_Kc},
                  sig} — everything EXCEPT S, written to
                  app/promo-meta.json and bundled into the app.
  The app re-derives S from the typed code, rebuilds the license,
  and checks sig + unwraps Kc exactly like a minted key; a wrong
  code fails the signature check before any decryption is tried.
  The code itself is never stored in, or recoverable from, anything
  that ships. A short code is guessable in principle — the cost
  imposed is the 600k-iteration KDF, the app throttles repeated
  failures, and revocation is a tooling change + pack rebuild.
  Concealment honesty: the sealed built-in is obfuscation-grade —
  anyone who reads this tooling's source can reconstruct the
  digits with effort. That is acceptable because this file is
  owner-side only (never bundled, never shipped); the shipped
  artifacts contain no trace of the code, sealed or otherwise.
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_KEYDIR = os.path.expanduser("~/.hackproof")
WRAP_INFO = b"hackproof-wrap"

# --- Promo / test access ---------------------------------------------
# The promo code is BUILT INTO this tooling in concealed form (see
# _PROMO_SEALED below): build-pack derives the promo license from
# it automatically on every build — no config file, no mint step —
# and writes the public metadata to app/promo-meta.json for the
# app bundler. The digits never appear in plaintext in this repo,
# the shipped site, or the app; the shipped artifacts carry only
# the derived metadata (salt, wrapped key, signature).
PROMO_META_NAME = "promo-meta.json"
PROMO_KDF = "PBKDF2-HMAC-SHA256"
PROMO_KDF_ITERATIONS = 600_000
PROMO_DAYS = 3650

# The built-in promo code, sealed. Construction: the digits were
# encrypted with AES-256-GCM under a random 32-byte key; the key
# is stored XOR-masked with SHA-256 of the label string below, and
# the sealed blob is nonce || ciphertext. Neither hex string IS
# the code, and the literal digits appear nowhere in this file.
# To ROTATE the code: regenerate both strings for the new digits
# (same construction) and rebuild the pack. To RETIRE the code:
# delete both strings (leave them empty) and rebuild the pack —
# build-pack then writes null metadata and the code stops working
# in every edition built from that tree.
_PROMO_KEY_LABEL = b"hackproof-promo-tooling-v1"
_PROMO_KEY_MASKED = bytes.fromhex(
    "2c7b42e77629253cf1b4199d6d2faa48"
    "41fd56ace1c68518689d4d00a3cc303d")
_PROMO_SEALED = bytes.fromhex(
    "cda5f128080eb7b78e0a77554df8ca1a"
    "b9f6a746f41f25b4798a316daf12b1e2")


def _builtin_promo_code():
    """The built-in promo code, unsealed — or None when the
    built-in has been removed (the retire-the-code state)."""
    if not _PROMO_KEY_MASKED or not _PROMO_SEALED:
        return None
    _, AESGCM, _, _ = need_crypto()
    mask = hashlib.sha256(_PROMO_KEY_LABEL).digest()
    key = bytes(a ^ b for a, b in zip(_PROMO_KEY_MASKED, mask))
    code = AESGCM(key).decrypt(
        _PROMO_SEALED[:12], _PROMO_SEALED[12:], None).decode("utf-8")
    if not (code.isdigit() and 4 <= len(code) <= 12):
        sys.exit("REFUSING: the sealed promo built-in did not unseal "
                 "to a valid code — the tooling is damaged; restore "
                 "it before building a pack.")
    return code


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
    # Write with final permissions from the first byte — a plain open()
    # would leave the secrets at umask defaults until the chmod below.
    def _write_new(path, data, mode):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    _write_new(paths["priv"], seed, 0o600)
    _write_new(paths["pub"], pub, 0o644)
    _write_new(paths["kc"], kc, 0o600)
    for p in (paths["priv"], paths["kc"]):
        os.chmod(p, 0o600)
    os.chmod(paths["pub"], 0o644)
    print("Wrote key material to %s (chmod 600 on secrets)" % keydir)
    print("  ed25519-private.key  <- NEVER commit, NEVER share")
    print("  content-master.key   <- NEVER commit, NEVER share")
    print("  ed25519-public.key    <- this one is public")
    print()
    print("STEP 2 — paste this PUBLIC key into BOTH files")
    print("  (game/index.html, shared.js — shared.js covers exam.html + verify.html):")
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
    # A non-positive --days mints a license that is already expired the
    # moment it is emailed to the customer; an absurd one overflows the
    # expiry the pages check. Refuse both (argparse only guarantees int).
    if not 1 <= days <= 3650:
        sys.exit("REFUSING: --days must be between 1 and 3650 (got %d) — "
                 "a license minted with that lifetime is dead on arrival "
                 "or nonsensical." % days)
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


def derive_promo_secret(code, salt):
    """S for the promo license: PBKDF2-HMAC-SHA256 over the code.
    The iteration count is the guessing cost — it ships in the
    metadata so every client pays it identically."""
    return hashlib.pbkdf2_hmac("sha256", code.encode("utf-8"), salt,
                               PROMO_KDF_ITERATIONS, dklen=32)


def build_promo_meta(priv, kc):
    """Construct the promo license and the public metadata the app
    reconstructs it from, deriving the secret from the SEALED
    BUILT-IN code. Returns None when the built-in has been removed
    (retired). The metadata carries everything EXCEPT the
    code-derived secret S: the KDF salt + parameters, the signed
    license fields, and the Ed25519 signature over them. Entering
    the right code re-derives S; the signature then verifies and
    the wrap unwraps. A wrong code fails the signature check,
    exactly like a forged license key."""
    code = _builtin_promo_code()
    if code is None:
        return None
    _, AESGCM, HKDF, hashes = need_crypto()
    import time
    salt = os.urandom(16)
    S = derive_promo_secret(code, salt)
    kw = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"",
              info=WRAP_INFO).derive(S)
    iv_w = os.urandom(12)
    wrapped = iv_w + AESGCM(kw).encrypt(iv_w, kc, None)
    lic = {
        "id": b64e(os.urandom(6)),
        "tier": "premium",
        "expiry": int(time.time()) + PROMO_DAYS * 86400,
        "S": b64e(S),
        "wrapped_Kc": b64e(wrapped),
    }
    sig = priv.sign(canonical_fields(lic).encode("utf-8"))
    return {
        "v": 1,
        "kdf": PROMO_KDF,
        "iterations": PROMO_KDF_ITERATIONS,
        "salt": b64e(salt),
        "license": {"id": lic["id"], "tier": lic["tier"],
                    "expiry": lic["expiry"],
                    "wrapped_Kc": lic["wrapped_Kc"]},
        "sig": b64e(sig),
    }


def promo_license_key(meta, S):
    """The full license key string a client reconstructs from the
    code + metadata (the pages/app rebuild this same string; it
    exists here so tests and audits have one reference form).
    Field order matches cmd_mint exactly."""
    lic = {"id": meta["license"]["id"], "tier": meta["license"]["tier"],
           "expiry": meta["license"]["expiry"], "S": b64e(S),
           "wrapped_Kc": meta["license"]["wrapped_Kc"],
           "sig": meta["sig"]}
    return b64e(json.dumps(lic, separators=(",", ":")).encode("utf-8"))


def cmd_build_pack(keydir, content_dir, game_dir):
    _, AESGCM, _, _ = need_crypto()
    priv, kc = load_keys(keydir)
    mod_dir = os.path.join(content_dir, "modules")
    if not os.path.isdir(mod_dir):
        sys.exit("Expected %s" % mod_dir)
    modules = []
    for fn in sorted(os.listdir(mod_dir)):
        if fn.endswith(".md"):
            with open(os.path.join(mod_dir, fn), encoding="utf-8") as f:
                modules.append({"file": fn, "body": f.read()})
    if len(modules) != 43:
        sys.exit("Expected 43 premium course module .md files, found %d"
                 % len(modules))
    pack = {"modules": modules}
    plaintext = json.dumps(pack, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    iv_p = os.urandom(12)
    blob = b64e(iv_p + AESGCM(kc).encrypt(iv_p, plaintext, None))
    # Promo: the sealed built-in code is baked into EVERY build —
    # no config, no switch. The metadata (everything except the
    # code-derived secret) is written to app/promo-meta.json, in
    # the app's own layer of the tree; the app bundler ships it
    # inside the app. The website is not part of this feature and
    # build-pack writes NO promo material into any page. If the
    # built-in has been removed (retired), the metadata is `null`
    # — a stale metadata file must never survive a rebuild.
    meta = build_promo_meta(priv, kc)
    meta_json = (json.dumps(meta, separators=(",", ":"))
                 if meta is not None else "null")
    repo_root = os.path.dirname(os.path.abspath(game_dir))
    meta_path = os.path.join(repo_root, "app", PROMO_META_NAME)
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(meta_json + "\n")
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
    print("Pack built: %d course modules, %d plaintext bytes" %
          (len(modules), len(plaintext)))
    print("  wrote %s" % b64_path)
    print("  inlined ciphertext into %s" % html_path)
    if meta is not None:
        print("  promo access: ENABLED — promo license id %s baked "
              "into the app metadata" % meta["license"]["id"])
        print("    (derived from the sealed built-in code; the code")
        print("     itself is never written anywhere)")
    else:
        print("  promo access: off (the sealed built-in has been "
              "removed)")
    print("  wrote %s" % meta_path)
    print("Commit + deploy both.")


def license_secret_from_key(pubkey, license_key):
    """Extract the per-license secret S from a student's license key.

    The key's own Ed25519 signature MUST verify against our public key —
    otherwise the S inside it is attacker-chosen and any HMAC "proof"
    built on it is meaningless. Returns (S, license id): the 32-byte S,
    plus the id sign-cert binds the certificate payload to.
    """
    clean = re.sub(r"\s+", "", license_key or "")
    try:
        lic = json.loads(base64.b64decode(clean).decode("utf-8"))
    except Exception:
        sys.exit("REFUSING: the --license key is not valid base64/JSON.")
    for k in ("id", "tier", "expiry", "S", "wrapped_Kc", "sig"):
        if k not in lic:
            sys.exit("REFUSING: the --license key is missing fields.")
    if lic.get("tier") != "premium":
        sys.exit("REFUSING: the --license key is not a premium license.")
    canonical = json.dumps(
        {"id": lic["id"], "tier": lic["tier"], "expiry": lic["expiry"],
         "S": lic["S"], "wrapped_Kc": lic["wrapped_Kc"]},
        separators=(",", ":"))
    try:
        sig = base64.b64decode(lic["sig"].encode("ascii"))
        pubkey.verify(sig, canonical.encode("utf-8"))
    except Exception:
        sys.exit("REFUSING: the --license key's signature does not verify — "
                 "not a genuine HackProof license.")
    try:
        S = base64.b64decode(lic["S"].encode("ascii"))
    except Exception:
        sys.exit("REFUSING: the --license key has a garbled S field.")
    if len(S) != 32:
        sys.exit("REFUSING: the --license key's S field is not 32 bytes.")
    return S, lic["id"]


def cmd_sign_cert(keydir, code, license_key):
    """Countersign a student's certificate code.

    The student emails you the UNSIGNED code from exam.html PLUS their
    premium license key. Before countersigning we now:

      1. Check the score fields describe a pass the exam page could
         actually have issued: integer score of 72-90 (of 90 questions;
         72 is the 80% pass mark) and pct exactly the percentage the
         exam computes from that score. A failing, impossible, or
         internally inconsistent payload is refused, even with a valid
         proof — the proof is computed with the student's OWN license
         secret, so a holder can make one for any payload they invent.
      2. Check the payload's lic_id names the very license key provided
         — the certificate must belong to the key that earned it.
      3. Verify the HMAC-SHA256 proof embedded by exam.html. The proof is
         HMAC_SHA256(per-license secret S, canonical payload), computed
         in the browser at the moment the exam was genuinely passed. S
         comes from the student's own license key, whose Ed25519
         signature we verify first so an attacker can't substitute
         their own S. Missing or bad proof -> REFUSED, no signature.

    Only then do we countersign with Ed25519 as before; exam.html /
    verify.html verify that signature against your public key.

    Byte-compatibility note: the browser verifies
    JSON.stringify(parsed_payload) — separators (",", ":"),
    key insertion order preserved, raw UTF-8. We reproduce
    exactly that here with separators=(",", ":") and
    ensure_ascii=False.
    """
    priv, _ = load_keys(keydir)
    pubkey = priv.public_key()
    clean = re.sub(r"\s+", "", code or "")
    try:
        payload = json.loads(base64.b64decode(clean).decode("utf-8"))
    except Exception:
        sys.exit("Not a valid certificate code (bad base64/JSON).")
    if (not isinstance(payload, dict) or payload.get("v") != 1
            or "cert_id" not in payload or "name" not in payload
            or "sig" in payload):
        sys.exit("Not an unsigned HackProof certificate payload.")
    # 1) score fields: integers (bool is not an int here), a passing
    # score the exam could have issued, and pct exactly consistent.
    for field in ("score", "pct"):
        val = payload.get(field)
        if isinstance(val, bool) or not isinstance(val, int):
            sys.exit("REFUSING: score field %r must be an integer "
                     "(got %r)." % (field, val))
    score, pct = payload["score"], payload["pct"]
    if not 72 <= score <= 90:
        sys.exit("REFUSING: score %r is not a passing exam score "
                 "(72-90 of 90)." % (score,))
    # Math.round(score / 90 * 100) with JS half-up rounding, in integers.
    expected_pct = (score * 200 + 90) // 180
    if pct != expected_pct:
        sys.exit("REFUSING: pct %r does not match score %r "
                 "(the exam would have issued %d)."
                 % (pct, score, expected_pct))
    # 3) HMAC-SHA256 proof — present, well-formed, and valid
    proof_b64 = payload.get("proof")
    if not isinstance(proof_b64, str) or not proof_b64:
        sys.exit("REFUSING: certificate code has no HMAC proof — it was not "
                 "generated by the current exam page. Ask the student to "
                 "re-generate the code from the updated exam.html.")
    if not license_key:
        sys.exit("REFUSING: sign-cert needs the student's license key "
                 "(--license) to verify the certificate's HMAC proof.")
    S, lic_id = license_secret_from_key(pubkey, license_key)
    # 2) the payload must name the very license that earned it
    if payload.get("lic_id") != lic_id:
        sys.exit("REFUSING: the certificate's lic_id %r does not match "
                 "the license key provided (%r) — code and key must "
                 "come from the same student."
                 % (payload.get("lic_id"), lic_id))
    # Re-canonicalize exactly what the browser HMAC'd: the payload
    # WITHOUT the proof field (proof was appended last, so dropping it
    # restores the original key order).
    body = {k: v for k, v in payload.items() if k != "proof"}
    canonical = json.dumps(body, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    try:
        proof = base64.b64decode(proof_b64.encode("ascii"))
    except Exception:
        sys.exit("REFUSING: proof is not valid base64.")
    expected = hmac.new(S, canonical, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, proof):
        sys.exit("REFUSING: HMAC proof does not verify — this payload was "
                 "hand-crafted, not produced by the exam with a genuine "
                 "license. No signature issued.")
    # 4) Exam integrity verdict — SURFACED, never silently enforced.
    # exam.html records local behavioral signals (tab switches, copy/cut
    # attempts, answer timing, duration) and embeds a verdict in the
    # payload. A flagged verdict does NOT refuse the certificate — the
    # seller sees it here and decides. Signals are heuristics, not proof
    # of AI use or cheating.
    integ = payload.get("integrity")
    if not isinstance(integ, dict) or "verdict" not in integ:
        print("INTEGRITY: not recorded (certificate generated by an older "
              "exam version — no integrity summary present).")
    elif integ.get("verdict") == "clean":
        print("INTEGRITY: CLEAN — tab switches: %s, copy attempts: %s, "
              "median answer time: %s ms, duration: %s s."
              % (integ.get("tab_switches"), integ.get("copy_attempts"),
                 integ.get("median_answer_ms"), integ.get("duration_s")))
    else:
        print()
        print("!" * 64)
        print("!! INTEGRITY WARNING — VERDICT: FLAGGED")
        print("!! Flags: %s" % ", ".join(integ.get("flags") or []))
        print("!! tab switches: %s | window blurs: %s | copy attempts: %s"
              " | cut attempts: %s | paste attempts: %s"
              % (integ.get("tab_switches"), integ.get("window_blurs"),
                 integ.get("copy_attempts"), integ.get("cut_attempts"),
                 integ.get("paste_attempts")))
        print("!! fast answers (<2s): %s | median answer time: %s ms"
              " | total duration: %s s"
              % (integ.get("fast_answers"), integ.get("median_answer_ms"),
                 integ.get("duration_s")))
        print("!! These are behavioral signals, not proof. The certificate")
        print("!! is still countersigned below — YOU decide whether to")
        print("!! issue it, ask the student to retake, or follow up.")
        print("!" * 64)
        print()
    canonical_full = json.dumps(payload, separators=(",", ":"),
                                ensure_ascii=False).encode("utf-8")
    sig = priv.sign(canonical_full)
    signed = {"payload": payload, "sig": b64e(sig)}
    out = b64e(json.dumps(signed, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))
    print("COUNTERSIGNED CERTIFICATE — email this to the student:")
    print(out)
    print()
    print("cert: %s  name: %s  score: %s/90 (%s%%)  date: %s" %
          (payload.get("cert_id"), payload.get("name"),
           payload.get("score"), payload.get("pct"), payload.get("date")))


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
    c = sub.add_parser("sign-cert", help="countersign a student's certificate code")
    c.add_argument("--keydir", default=DEFAULT_KEYDIR)
    c.add_argument("code", help="unsigned certificate code from the student (or - for stdin)")
    c.add_argument("--license", default=None,
                   help="the student's premium license key (or - for stdin); "
                        "required to verify the certificate's HMAC proof")
    args = ap.parse_args()
    if args.cmd == "setup":
        cmd_setup(args.keydir)
    elif args.cmd == "mint":
        cmd_mint(args.keydir, args.tier, args.days)
    elif args.cmd == "build-pack":
        cmd_build_pack(args.keydir, args.content, args.game)
    elif args.cmd == "sign-cert":
        code = args.code
        if code == "-":
            code = sys.stdin.read()
        lic = args.license
        if lic == "-":
            lic = sys.stdin.read()
        cmd_sign_cert(args.keydir, code, lic)


if __name__ == "__main__":
    main()
