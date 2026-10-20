/* ================================================================
   HackProof — shared.js
   Loaded by exam.html and verify.html (both pages need exactly the
   same CONFIG, vendored Ed25519 verifier, and license checker).
   Keeping ONE copy here means the public key and the crypto can
   never drift between the two pages, and the browser downloads
   this file once and caches it across both pages.
   Contents, in order: CONFIG / vendored Ed25519 (TweetNaCl) /
   License. game/index.html keeps its own full copy on purpose —
   the game also signs nothing but must unwrap the premium pack,
   and tools/keygen.py build-pack rewrites that file in place.
   ================================================================ */

"use strict";
/* ================= CONFIG ================= */
const CONFIG = {
  LICENSE_STORAGE_KEY: "hackproof_license_v1",
  EXAM_NAME_KEY: "hackproof_exam_name",
  PASS_PCT: 80,
  /* LICENSE_PUBLIC_KEY_HEX: Skyler pastes the public key here after running
     `python3 tools/keygen.py setup` (it prints the key). Until replaced,
     license checks stay locked. Same value as in game/index.html. This
     CONFIG lives in shared.js, so ONE paste covers exam.html + verify.html. */
  /* PRODUCTION KEY — rotated 2026-10-12. Matches the private signing key
     kept OFFLINE (never in this repo). See tools/keygen.py setup. */
  LICENSE_PUBLIC_KEY_HEX: "f8ff4f59627031e9e522aabed81c8eb208616db8b43843b96d6e55540897eda7",
  VERIFY_URL: "https://therealjesusthehacker.github.io/HackProof/verify.html"
};

/* ---------------- VENDORED ED25519 ----------------
   TweetNaCl (public domain): verify-only subset, byte-identical to
   game/index.html. No signing capability ships in this page — certificates
   are countersigned offline with tools/keygen.py; this page only verifies. */
(function(nacl) {
'use strict';
// Ed25519 verify-only subset of TweetNaCl (public domain) - nacl.sign.detached.verify path only.
var u64 = function(h, l) { this.hi = h|0 >>> 0; this.lo = l|0 >>> 0; };
var gf = function(init) {
  var i, r = new Float64Array(16);
  if (init) for (i = 0; i < init.length; i++) r[i] = init[i];
  return r;
};

//  Pluggable, initialized in high-level API below.
var randombytes = function(/* x, n */) { throw new Error('no PRNG'); };

var _0 = new Uint8Array(16);
var _9 = new Uint8Array(32); _9[0] = 9;

var gf0 = gf(),
    gf1 = gf([1]),
    _121665 = gf([0xdb41, 1]),
    D = gf([0x78a3, 0x1359, 0x4dca, 0x75eb, 0xd8ab, 0x4141, 0x0a4d, 0x0070, 0xe898, 0x7779, 0x4079, 0x8cc7, 0xfe73, 0x2b6f, 0x6cee, 0x5203]),
    D2 = gf([0xf159, 0x26b2, 0x9b94, 0xebd6, 0xb156, 0x8283, 0x149a, 0x00e0, 0xd130, 0xeef3, 0x80f2, 0x198e, 0xfce7, 0x56df, 0xd9dc, 0x2406]),
    X = gf([0xd51a, 0x8f25, 0x2d60, 0xc956, 0xa7b2, 0x9525, 0xc760, 0x692c, 0xdc5c, 0xfdd6, 0xe231, 0xc0a4, 0x53fe, 0xcd6e, 0x36d3, 0x2169]),
    Y = gf([0x6658, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666, 0x6666]),
    I = gf([0xa0b0, 0x4a0e, 0x1b27, 0xc4ee, 0xe478, 0xad2f, 0x1806, 0x2f43, 0xd7a7, 0x3dfb, 0x0099, 0x2b4d, 0xdf0b, 0x4fc1, 0x2480, 0x2b83]);

function L32(x, c) { return (x << c) | (x >>> (32 - c)); }

function ld32(x, i) {
  var u = x[i+3] & 0xff;
  u = (u<<8)|(x[i+2] & 0xff);
  u = (u<<8)|(x[i+1] & 0xff);
  return (u<<8)|(x[i+0] & 0xff);
}

function dl64(x, i) {
  var h = (x[i] << 24) | (x[i+1] << 16) | (x[i+2] << 8) | x[i+3];
  var l = (x[i+4] << 24) | (x[i+5] << 16) | (x[i+6] << 8) | x[i+7];
  return new u64(h, l);
}

function st32(x, j, u) {
  var i;
  for (i = 0; i < 4; i++) { x[j+i] = u & 255; u >>>= 8; }
}

function ts64(x, i, u) {
  x[i]   = (u.hi >> 24) & 0xff;
  x[i+1] = (u.hi >> 16) & 0xff;
  x[i+2] = (u.hi >>  8) & 0xff;
  x[i+3] = u.hi & 0xff;
  x[i+4] = (u.lo >> 24)  & 0xff;
  x[i+5] = (u.lo >> 16)  & 0xff;
  x[i+6] = (u.lo >>  8)  & 0xff;
  x[i+7] = u.lo & 0xff;
}

function vn(x, xi, y, yi, n) {
  var i,d = 0;
  for (i = 0; i < n; i++) d |= x[xi+i]^y[yi+i];
  return (1 & ((d - 1) >>> 8)) - 1;
}

function crypto_verify_16(x, xi, y, yi) {
  return vn(x,xi,y,yi,16);
}

function crypto_verify_32(x, xi, y, yi) {
  return vn(x,xi,y,yi,32);
}

function set25519(r, a) {
  var i;
  for (i = 0; i < 16; i++) r[i] = a[i]|0;
}

function car25519(o) {
  var c;
  var i;
  for (i = 0; i < 16; i++) {
      o[i] += 65536;
      c = Math.floor(o[i] / 65536);
      o[(i+1)*(i<15?1:0)] += c - 1 + 37 * (c-1) * (i===15?1:0);
      o[i] -= (c * 65536);
  }
}

function sel25519(p, q, b) {
  var t, c = ~(b-1);
  for (var i = 0; i < 16; i++) {
    t = c & (p[i] ^ q[i]);
    p[i] ^= t;
    q[i] ^= t;
  }
}

function pack25519(o, n) {
  var i, j, b;
  var m = gf(), t = gf();
  for (i = 0; i < 16; i++) t[i] = n[i];
  car25519(t);
  car25519(t);
  car25519(t);
  for (j = 0; j < 2; j++) {
    m[0] = t[0] - 0xffed;
    for (i = 1; i < 15; i++) {
      m[i] = t[i] - 0xffff - ((m[i-1]>>16) & 1);
      m[i-1] &= 0xffff;
    }
    m[15] = t[15] - 0x7fff - ((m[14]>>16) & 1);
    b = (m[15]>>16) & 1;
    m[14] &= 0xffff;
    sel25519(t, m, 1-b);
  }
  for (i = 0; i < 16; i++) {
    o[2*i] = t[i] & 0xff;
    o[2*i+1] = t[i]>>8;
  }
}

function neq25519(a, b) {
  var c = new Uint8Array(32), d = new Uint8Array(32);
  pack25519(c, a);
  pack25519(d, b);
  return crypto_verify_32(c, 0, d, 0);
}

function par25519(a) {
  var d = new Uint8Array(32);
  pack25519(d, a);
  return d[0] & 1;
}

function unpack25519(o, n) {
  var i;
  for (i = 0; i < 16; i++) o[i] = n[2*i] + (n[2*i+1] << 8);
  o[15] &= 0x7fff;
}

function A(o, a, b) {
  var i;
  for (i = 0; i < 16; i++) o[i] = (a[i] + b[i])|0;
}

function Z(o, a, b) {
  var i;
  for (i = 0; i < 16; i++) o[i] = (a[i] - b[i])|0;
}

function M(o, a, b) {
  var i, j, t = new Float64Array(31);
  for (i = 0; i < 31; i++) t[i] = 0;
  for (i = 0; i < 16; i++) {
    for (j = 0; j < 16; j++) {
      t[i+j] += a[i] * b[j];
    }
  }
  for (i = 0; i < 15; i++) {
    t[i] += 38 * t[i+16];
  }
  for (i = 0; i < 16; i++) o[i] = t[i];
  car25519(o);
  car25519(o);
}

function S(o, a) {
  M(o, a, a);
}

function inv25519(o, i) {
  var c = gf();
  var a;
  for (a = 0; a < 16; a++) c[a] = i[a];
  for (a = 253; a >= 0; a--) {
    S(c, c);
    if(a !== 2 && a !== 4) M(c, c, i);
  }
  for (a = 0; a < 16; a++) o[a] = c[a];
}

function pow2523(o, i) {
  var c = gf();
  var a;
  for (a = 0; a < 16; a++) c[a] = i[a];
  for (a = 250; a >= 0; a--) {
      S(c, c);
      if(a !== 1) M(c, c, i);
  }
  for (a = 0; a < 16; a++) o[a] = c[a];
}

function add64() {
  var a = 0, b = 0, c = 0, d = 0, m16 = 65535, l, h, i;
  for (i = 0; i < arguments.length; i++) {
    l = arguments[i].lo;
    h = arguments[i].hi;
    a += (l & m16); b += (l >>> 16);
    c += (h & m16); d += (h >>> 16);
  }

  b += (a >>> 16);
  c += (b >>> 16);
  d += (c >>> 16);

  return new u64((c & m16) | (d << 16), (a & m16) | (b << 16));
}

function shr64(x, c) {
  return new u64((x.hi >>> c), (x.lo >>> c) | (x.hi << (32 - c)));
}

function xor64() {
  var l = 0, h = 0, i;
  for (i = 0; i < arguments.length; i++) {
    l ^= arguments[i].lo;
    h ^= arguments[i].hi;
  }
  return new u64(h, l);
}

function R(x, c) {
  var h, l, c1 = 32 - c;
  if (c < 32) {
    h = (x.hi >>> c) | (x.lo << c1);
    l = (x.lo >>> c) | (x.hi << c1);
  } else if (c < 64) {
    h = (x.lo >>> c) | (x.hi << c1);
    l = (x.hi >>> c) | (x.lo << c1);
  }
  return new u64(h, l);
}

function Ch(x, y, z) {
  var h = (x.hi & y.hi) ^ (~x.hi & z.hi),
      l = (x.lo & y.lo) ^ (~x.lo & z.lo);
  return new u64(h, l);
}

function Maj(x, y, z) {
  var h = (x.hi & y.hi) ^ (x.hi & z.hi) ^ (y.hi & z.hi),
      l = (x.lo & y.lo) ^ (x.lo & z.lo) ^ (y.lo & z.lo);
  return new u64(h, l);
}

function Sigma0(x) { return xor64(R(x,28), R(x,34), R(x,39)); }
function Sigma1(x) { return xor64(R(x,14), R(x,18), R(x,41)); }
function sigma0(x) { return xor64(R(x, 1), R(x, 8), shr64(x,7)); }
function sigma1(x) { return xor64(R(x,19), R(x,61), shr64(x,6)); }

var K = [
  new u64(0x428a2f98, 0xd728ae22), new u64(0x71374491, 0x23ef65cd),
  new u64(0xb5c0fbcf, 0xec4d3b2f), new u64(0xe9b5dba5, 0x8189dbbc),
  new u64(0x3956c25b, 0xf348b538), new u64(0x59f111f1, 0xb605d019),
  new u64(0x923f82a4, 0xaf194f9b), new u64(0xab1c5ed5, 0xda6d8118),
  new u64(0xd807aa98, 0xa3030242), new u64(0x12835b01, 0x45706fbe),
  new u64(0x243185be, 0x4ee4b28c), new u64(0x550c7dc3, 0xd5ffb4e2),
  new u64(0x72be5d74, 0xf27b896f), new u64(0x80deb1fe, 0x3b1696b1),
  new u64(0x9bdc06a7, 0x25c71235), new u64(0xc19bf174, 0xcf692694),
  new u64(0xe49b69c1, 0x9ef14ad2), new u64(0xefbe4786, 0x384f25e3),
  new u64(0x0fc19dc6, 0x8b8cd5b5), new u64(0x240ca1cc, 0x77ac9c65),
  new u64(0x2de92c6f, 0x592b0275), new u64(0x4a7484aa, 0x6ea6e483),
  new u64(0x5cb0a9dc, 0xbd41fbd4), new u64(0x76f988da, 0x831153b5),
  new u64(0x983e5152, 0xee66dfab), new u64(0xa831c66d, 0x2db43210),
  new u64(0xb00327c8, 0x98fb213f), new u64(0xbf597fc7, 0xbeef0ee4),
  new u64(0xc6e00bf3, 0x3da88fc2), new u64(0xd5a79147, 0x930aa725),
  new u64(0x06ca6351, 0xe003826f), new u64(0x14292967, 0x0a0e6e70),
  new u64(0x27b70a85, 0x46d22ffc), new u64(0x2e1b2138, 0x5c26c926),
  new u64(0x4d2c6dfc, 0x5ac42aed), new u64(0x53380d13, 0x9d95b3df),
  new u64(0x650a7354, 0x8baf63de), new u64(0x766a0abb, 0x3c77b2a8),
  new u64(0x81c2c92e, 0x47edaee6), new u64(0x92722c85, 0x1482353b),
  new u64(0xa2bfe8a1, 0x4cf10364), new u64(0xa81a664b, 0xbc423001),
  new u64(0xc24b8b70, 0xd0f89791), new u64(0xc76c51a3, 0x0654be30),
  new u64(0xd192e819, 0xd6ef5218), new u64(0xd6990624, 0x5565a910),
  new u64(0xf40e3585, 0x5771202a), new u64(0x106aa070, 0x32bbd1b8),
  new u64(0x19a4c116, 0xb8d2d0c8), new u64(0x1e376c08, 0x5141ab53),
  new u64(0x2748774c, 0xdf8eeb99), new u64(0x34b0bcb5, 0xe19b48a8),
  new u64(0x391c0cb3, 0xc5c95a63), new u64(0x4ed8aa4a, 0xe3418acb),
  new u64(0x5b9cca4f, 0x7763e373), new u64(0x682e6ff3, 0xd6b2b8a3),
  new u64(0x748f82ee, 0x5defb2fc), new u64(0x78a5636f, 0x43172f60),
  new u64(0x84c87814, 0xa1f0ab72), new u64(0x8cc70208, 0x1a6439ec),
  new u64(0x90befffa, 0x23631e28), new u64(0xa4506ceb, 0xde82bde9),
  new u64(0xbef9a3f7, 0xb2c67915), new u64(0xc67178f2, 0xe372532b),
  new u64(0xca273ece, 0xea26619c), new u64(0xd186b8c7, 0x21c0c207),
  new u64(0xeada7dd6, 0xcde0eb1e), new u64(0xf57d4f7f, 0xee6ed178),
  new u64(0x06f067aa, 0x72176fba), new u64(0x0a637dc5, 0xa2c898a6),
  new u64(0x113f9804, 0xbef90dae), new u64(0x1b710b35, 0x131c471b),
  new u64(0x28db77f5, 0x23047d84), new u64(0x32caab7b, 0x40c72493),
  new u64(0x3c9ebe0a, 0x15c9bebc), new u64(0x431d67c4, 0x9c100d4c),
  new u64(0x4cc5d4be, 0xcb3e42b6), new u64(0x597f299c, 0xfc657e2a),
  new u64(0x5fcb6fab, 0x3ad6faec), new u64(0x6c44198c, 0x4a475817)
];

function crypto_hashblocks(x, m, n) {
  var z = [], b = [], a = [], w = [], t, i, j;

  for (i = 0; i < 8; i++) z[i] = a[i] = dl64(x, 8*i);

  var pos = 0;
  while (n >= 128) {
    for (i = 0; i < 16; i++) w[i] = dl64(m, 8*i+pos);
    for (i = 0; i < 80; i++) {
      for (j = 0; j < 8; j++) b[j] = a[j];
      t = add64(a[7], Sigma1(a[4]), Ch(a[4], a[5], a[6]), K[i], w[i%16]);
      b[7] = add64(t, Sigma0(a[0]), Maj(a[0], a[1], a[2]));
      b[3] = add64(b[3], t);
      for (j = 0; j < 8; j++) a[(j+1)%8] = b[j];
      if (i%16 === 15) {
        for (j = 0; j < 16; j++) {
          w[j] = add64(w[j], w[(j+9)%16], sigma0(w[(j+1)%16]), sigma1(w[(j+14)%16]));
        }
      }
    }

    for (i = 0; i < 8; i++) {
      a[i] = add64(a[i], z[i]);
      z[i] = a[i];
    }

    pos += 128;
    n -= 128;
  }

  for (i = 0; i < 8; i++) ts64(x, 8*i, z[i]);
  return n;
}

var iv = new Uint8Array([
  0x6a,0x09,0xe6,0x67,0xf3,0xbc,0xc9,0x08,
  0xbb,0x67,0xae,0x85,0x84,0xca,0xa7,0x3b,
  0x3c,0x6e,0xf3,0x72,0xfe,0x94,0xf8,0x2b,
  0xa5,0x4f,0xf5,0x3a,0x5f,0x1d,0x36,0xf1,
  0x51,0x0e,0x52,0x7f,0xad,0xe6,0x82,0xd1,
  0x9b,0x05,0x68,0x8c,0x2b,0x3e,0x6c,0x1f,
  0x1f,0x83,0xd9,0xab,0xfb,0x41,0xbd,0x6b,
  0x5b,0xe0,0xcd,0x19,0x13,0x7e,0x21,0x79
]);

function crypto_hash(out, m, n) {
  var h = new Uint8Array(64), x = new Uint8Array(256);
  var i, b = n;

  for (i = 0; i < 64; i++) h[i] = iv[i];

  crypto_hashblocks(h, m, n);
  n %= 128;

  for (i = 0; i < 256; i++) x[i] = 0;
  for (i = 0; i < n; i++) x[i] = m[b-n+i];
  x[n] = 128;

  n = 256-128*(n<112?1:0);
  x[n-9] = 0;
  ts64(x, n-8, new u64((b / 0x20000000) | 0, b << 3));
  crypto_hashblocks(h, x, n);

  for (i = 0; i < 64; i++) out[i] = h[i];

  return 0;
}
function add(p, q) {
  var a = gf(), b = gf(), c = gf(),
      d = gf(), e = gf(), f = gf(),
      g = gf(), h = gf(), t = gf();

  Z(a, p[1], p[0]);
  Z(t, q[1], q[0]);
  M(a, a, t);
  A(b, p[0], p[1]);
  A(t, q[0], q[1]);
  M(b, b, t);
  M(c, p[3], q[3]);
  M(c, c, D2);
  M(d, p[2], q[2]);
  A(d, d, d);
  Z(e, b, a);
  Z(f, d, c);
  A(g, d, c);
  A(h, b, a);

  M(p[0], e, f);
  M(p[1], h, g);
  M(p[2], g, f);
  M(p[3], e, h);
}

function cswap(p, q, b) {
  var i;
  for (i = 0; i < 4; i++) {
    sel25519(p[i], q[i], b);
  }
}

function pack(r, p) {
  var tx = gf(), ty = gf(), zi = gf();
  inv25519(zi, p[2]);
  M(tx, p[0], zi);
  M(ty, p[1], zi);
  pack25519(r, ty);
  r[31] ^= par25519(tx) << 7;
}

function scalarmult(p, q, s) {
  var b, i;
  set25519(p[0], gf0);
  set25519(p[1], gf1);
  set25519(p[2], gf1);
  set25519(p[3], gf0);
  for (i = 255; i >= 0; --i) {
    b = (s[(i/8)|0] >> (i&7)) & 1;
    cswap(p, q, b);
    add(q, p);
    add(p, p);
    cswap(p, q, b);
  }
}

function scalarbase(p, s) {
  var q = [gf(), gf(), gf(), gf()];
  set25519(q[0], X);
  set25519(q[1], Y);
  set25519(q[2], gf1);
  M(q[3], X, Y);
  scalarmult(p, q, s);
}

var L = new Float64Array([0xed, 0xd3, 0xf5, 0x5c, 0x1a, 0x63, 0x12, 0x58, 0xd6, 0x9c, 0xf7, 0xa2, 0xde, 0xf9, 0xde, 0x14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x10]);
function modL(r, x) {
  var carry, i, j, k;
  for (i = 63; i >= 32; --i) {
    carry = 0;
    for (j = i - 32, k = i - 12; j < k; ++j) {
      x[j] += carry - 16 * x[i] * L[j - (i - 32)];
      carry = Math.floor((x[j] + 128) / 256);
      x[j] -= carry * 256;
    }
    x[j] += carry;
    x[i] = 0;
  }
  carry = 0;
  for (j = 0; j < 32; j++) {
    x[j] += carry - (x[31] >> 4) * L[j];
    carry = x[j] >> 8;
    x[j] &= 255;
  }
  for (j = 0; j < 32; j++) x[j] -= carry * L[j];
  for (i = 0; i < 32; i++) {
    x[i+1] += x[i] >> 8;
    r[i] = x[i] & 255;
  }
}

function reduce(r) {
  var x = new Float64Array(64), i;
  for (i = 0; i < 64; i++) x[i] = r[i];
  for (i = 0; i < 64; i++) r[i] = 0;
  modL(r, x);
}

// Note: difference from C - smlen returned, not passed as argument.
function unpackneg(r, p) {
  var t = gf(), chk = gf(), num = gf(),
      den = gf(), den2 = gf(), den4 = gf(),
      den6 = gf();

  set25519(r[2], gf1);
  unpack25519(r[1], p);
  S(num, r[1]);
  M(den, num, D);
  Z(num, num, r[2]);
  A(den, r[2], den);

  S(den2, den);
  S(den4, den2);
  M(den6, den4, den2);
  M(t, den6, num);
  M(t, t, den);

  pow2523(t, t);
  M(t, t, num);
  M(t, t, den);
  M(t, t, den);
  M(r[0], t, den);

  S(chk, r[0]);
  M(chk, chk, den);
  if (neq25519(chk, num)) M(r[0], r[0], I);

  S(chk, r[0]);
  M(chk, chk, den);
  if (neq25519(chk, num)) return -1;

  if (par25519(r[0]) === (p[31]>>7)) Z(r[0], gf0, r[0]);

  M(r[3], r[0], r[1]);
  return 0;
}

function crypto_sign_open(m, sm, n, pk) {
  var i;
  var t = new Uint8Array(32), h = new Uint8Array(64);
  var p = [gf(), gf(), gf(), gf()],
      q = [gf(), gf(), gf(), gf()];

  if (n < 64) return -1;

  if (unpackneg(q, pk)) return -1;

  for (i = 0; i < n; i++) m[i] = sm[i];
  for (i = 0; i < 32; i++) m[i+32] = pk[i];
  crypto_hash(h, m, n);
  reduce(h);
  scalarmult(p, q, h);

  scalarbase(q, sm.subarray(32));
  add(p, q);
  pack(t, p);

  n -= 64;
  if (crypto_verify_32(sm, 0, t, 0)) {
    for (i = 0; i < n; i++) m[i] = 0;
    return -1;
  }

  for (i = 0; i < n; i++) m[i] = sm[i + 64];
  return n;
}

nacl.sign = {};
nacl.sign.detached = {};
nacl.sign.detached.verify = function(msg, sig, publicKey) {
  if (!(msg instanceof Uint8Array) || !(sig instanceof Uint8Array) || !(publicKey instanceof Uint8Array))
    throw new Error('bad input type');
  if (sig.length !== 64) throw new Error('bad signature size');
  if (publicKey.length !== 32) throw new Error('bad public key size');
  var sm = new Uint8Array(64 + msg.length);
  var m = new Uint8Array(64 + msg.length);
  var i;
  for (i = 0; i < 64; i++) sm[i] = sig[i];
  for (i = 0; i < msg.length; i++) sm[i+64] = msg[i];
  return (crypto_sign_open(m, sm, sm.length, publicKey) >= 0);
};
})(typeof module !== 'undefined' && module.exports ? module.exports : (self.nacl = self.nacl || {}));
/* Explicit binding for the vendored Ed25519 above (same as game/index.html).
   The IIFE attaches its API to `self.nacl` in browsers (an implicit global) or to
   `module.exports` under bundlers — the license code below must not rely
   on the implicit-global fallback to find it. This resolves to the same
   object in browsers; anywhere else it fails closed (null -> the verify
   try/catch reports "Signature check failed", never grants access). */
var nacl = (typeof self !== "undefined" && self.nacl && self.nacl.sign) ? self.nacl
  : (typeof module !== "undefined" && module.exports && module.exports.sign) ? module.exports
  : null;


/* ---------------- LICENSE (exam needs verification only) ----------------
   Same scheme as game/index.html: Ed25519-signed license, offline check.
   verifyLicense returns {tier, expiry, S (32-byte secret), wrappedKc}. */
const License = (() => {
  function b64ToBytes(s) {
    const bin = atob(s);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function hexToBytes(h) {
    if (typeof h !== "string" || !/^[0-9a-fA-F]+$/.test(h) || h.length !== 64)
      throw new Error("bad public key");
    const out = new Uint8Array(32);
    for (let i = 0; i < 32; i++) out[i] = parseInt(h.substr(i * 2, 2), 16);
    return out;
  }
  function te(s) { return new TextEncoder().encode(s); }
  function parseLicense(str) {
    const clean = (str || "").trim().replace(/\s+/g, "");
    if (!clean) throw new Error("Paste your premium license key first.");
    let obj;
    try { obj = JSON.parse(new TextDecoder().decode(b64ToBytes(clean))); }
    catch (e) { throw new Error("That key is garbled — check for typos and try again."); }
    for (const k of ["id", "tier", "expiry", "S", "wrapped_Kc", "sig"])
      if (typeof obj[k] === "undefined") throw new Error("That key is missing fields.");
    return obj;
  }
  function canonicalFields(lic) {
    return JSON.stringify({ id: lic.id, tier: lic.tier, expiry: lic.expiry, S: lic.S, wrapped_Kc: lic.wrapped_Kc });
  }
  /**
   * Clock-rollback guard (anti-license-resurrection).
   * Expiry checks use the device clock, which can be rewound to resurrect an
   * expired license. Record the highest device clock ever seen at a
   * *successful* verify in localStorage; refuse validation when the current
   * clock has moved backward more than 24h from that high-water mark. 24h of
   * slack tolerates DST / timezone changes while stopping casual rollback.
   * If storage is unavailable (e.g. private mode) the expiry check alone
   * applies — the guard simply can't persist its high-water mark.
   */
  const CLOCK_GUARD_KEY = "hackproof_max_clock";
  const CLOCK_GUARD_TOLERANCE_MS = 24 * 60 * 60 * 1000;
  function clockGuard(now) {
    let highWater = 0;
    try { highWater = parseInt(localStorage.getItem(CLOCK_GUARD_KEY) || "0", 10) || 0; } catch (e) { /* storage unavailable */ }
    if (highWater && now < highWater - CLOCK_GUARD_TOLERANCE_MS)
      throw new Error("Your device clock moved backward past the last verified time — restore the correct date and time to use your license.");
    try { if (now > highWater) localStorage.setItem(CLOCK_GUARD_KEY, String(now)); } catch (e) { /* storage unavailable */ }
  }
  async function verifyLicense(licenseStr, pubkeyHex) {
    if (!pubkeyHex || pubkeyHex.indexOf("REPLACE_WITH") === 0)
      throw new Error("This build isn't linked to licensing yet — check back soon.");
    const lic = parseLicense(licenseStr);
    if (lic.tier !== "premium") throw new Error("The exam requires a PREMIUM license.");
    const msg = te(canonicalFields(lic));
    const pk = hexToBytes(pubkeyHex);
    let ok = false;
    /* Decode the signature inside the try: a hand-crafted key whose sig
       field isn't valid base64 must get the same friendly verdict as any
       other forgery, not a raw atob DOMException. */
    try { ok = nacl.sign.detached.verify(msg, b64ToBytes(lic.sig), pk); }
    catch (e) { throw new Error("Signature check failed — that key isn't genuine."); }
    if (!ok) throw new Error("Signature check failed — that key isn't genuine.");
    const now = Date.now();
    if (typeof lic.expiry !== "number" || lic.expiry * 1000 <= now)
      throw new Error("This license has expired.");
    clockGuard(now); // successful verify: record device-clock high-water mark
    return { id: lic.id, tier: lic.tier, expiry: lic.expiry, S: b64ToBytes(lic.S) };
  }
  return { parseLicense, canonicalFields, verifyLicense, b64ToBytes, hexToBytes };
})();

/* ---------------- PROMO / TEST ACCESS ----------------
   The promo license is a REAL license (see tools/keygen.py): its
   secret S is PBKDF2-HMAC-SHA256(code, salt) instead of random,
   and the pack build publishes everything except S as
   promo-meta.json (KDF salt, signed license fields, signature) —
   the code itself is never in any shipped file. Reconstructing
   the license from a typed code is: derive S, rebuild the exact
   license object, check the Ed25519 signature. A wrong code
   derives the wrong S and fails the signature, exactly like a
   forged key. The course page carries the same metadata inlined
   (it must work from file://); here the exam fetches the JSON.
   Attempt throttling shares its localStorage keys with the
   course page, so failures count across both. */
const Promo = (() => {
  const FAIL_KEY = "hackproof_promo_fails";
  function bytesToB64(bytes) {
    let bin = "";
    const CHUNK = 0x8000;
    for (let i = 0; i < bytes.length; i += CHUNK)
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
    return btoa(bin);
  }
  async function fetchMeta() {
    try {
      const r = await fetch("promo-meta.json", { cache: "no-store" });
      if (!r || !r.ok) return null;
      const j = await r.json();
      return (j && typeof j === "object") ? j : null;
    } catch (e) { return null; }
  }
  async function derivePromoKey(code, meta, pubkeyHex) {
    const INACTIVE = "Promo codes aren't active right now — enter a license key instead, or ask Sentinel Safeguard about the code.";
    if (!meta || typeof meta !== "object") throw new Error(INACTIVE);
    const clean = (code || "").trim();
    if (!clean) throw new Error("Enter your promo / test code first.");
    const lm = meta.license;
    if (meta.v !== 1 || meta.kdf !== "PBKDF2-HMAC-SHA256" ||
        !lm || typeof lm !== "object" ||
        typeof lm.id !== "string" || lm.tier !== "premium" ||
        typeof lm.expiry !== "number" ||
        typeof lm.wrapped_Kc !== "string" ||
        typeof meta.salt !== "string" || typeof meta.sig !== "string" ||
        typeof meta.iterations !== "number" ||
        !(meta.iterations >= 1 && meta.iterations <= 10000000))
      throw new Error(INACTIVE);
    let salt, sigBytes;
    try { salt = License.b64ToBytes(meta.salt); sigBytes = License.b64ToBytes(meta.sig); }
    catch (e) { throw new Error(INACTIVE); }
    if (salt.length !== 16 || sigBytes.length !== 64)
      throw new Error(INACTIVE);
    if (typeof crypto === "undefined" || !crypto.subtle)
      throw new Error("This browser can't run the cryptographic check the code needs — open this page over HTTPS in a current browser.");
    const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(clean), "PBKDF2", false, ["deriveBits"]);
    const sBits = await crypto.subtle.deriveBits(
      { name: "PBKDF2", salt: salt, iterations: meta.iterations, hash: "SHA-256" },
      base, 256);
    const lic = { id: lm.id, tier: lm.tier, expiry: lm.expiry,
                  S: bytesToB64(new Uint8Array(sBits)), wrapped_Kc: lm.wrapped_Kc };
    const msg = new TextEncoder().encode(License.canonicalFields(lic));
    const pk = License.hexToBytes(pubkeyHex);
    let ok = false;
    try { ok = nacl.sign.detached.verify(msg, sigBytes, pk); }
    catch (e) { ok = false; }
    if (!ok) throw new Error("That code didn't work — check the digits and try again.");
    return btoa(JSON.stringify({ id: lic.id, tier: lic.tier, expiry: lic.expiry,
                                 S: lic.S, wrapped_Kc: lic.wrapped_Kc, sig: meta.sig }));
  }
  /* Throttle: after the n-th failure the wait is 5s, 10s, 20s,
     ... capped at 300s, counted from the last failure. */
  function failState() {
    try {
      const raw = JSON.parse(localStorage.getItem(FAIL_KEY) || "null");
      if (raw && typeof raw.count === "number" && typeof raw.last === "number")
        return raw;
    } catch (e) {}
    return { count: 0, last: 0 };
  }
  function waitSeconds(count) {
    if (!count || count < 1) return 0;
    return Math.min(5 * Math.pow(2, count - 1), 300);
  }
  function throttleRemaining() {
    const st = failState();
    const wait = waitSeconds(st.count);
    if (!wait || !st.last) return 0;
    const left = wait - (Date.now() - st.last) / 1000;
    return left > 0 ? Math.ceil(left) : 0;
  }
  function noteFailure() {
    const st = failState();
    try {
      localStorage.setItem(FAIL_KEY,
        JSON.stringify({ count: st.count + 1, last: Date.now() }));
    } catch (e) {}
  }
  function resetFailures() {
    try { localStorage.removeItem(FAIL_KEY); } catch (e) {}
  }
  return { fetchMeta, derivePromoKey, throttleRemaining, noteFailure, resetFailures };
})();
