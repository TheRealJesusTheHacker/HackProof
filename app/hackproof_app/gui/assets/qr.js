/* ================================================================
   HackProof app asset — QR rendering for the native Buy screen.
   This is the app copy of the website's own clean-room QR encoder
   (game/buy.html: "HackProof QR encoder", no third-party code), so
   a payment QR rendered inside the app is byte-identical to the
   one the website shows. Public API: HP_QR.encode(text) and
   hpQRDataURL(text, cellSize, margin).
   ================================================================ */
"use strict";
/* HackProof QR encoder — original clean-room implementation.
   Byte mode, error correction level M, automatic version selection (1-10).
   No third-party code. Public API: HP_QR.encode(text) -> {size, dark(r,c)} */

var HP_QR = (function () {
  "use strict";

  // [ecCodewordsPerBlock, [ [blockCount, dataCodewords], ... ] ] per version (EC level M)
  var BLOCKS = {
    1: [10, [[1, 16]]],
    2: [16, [[1, 28]]],
    3: [26, [[1, 44]]],
    4: [18, [[2, 32]]],
    5: [24, [[2, 43]]],
    6: [16, [[4, 27]]],
    7: [18, [[4, 31]]],
    8: [22, [[2, 38], [2, 39]]],
    9: [22, [[3, 36], [2, 37]]],
    10: [26, [[4, 43], [1, 44]]]
  };
  var ALIGN = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]
  };
  var REM_BITS = { 1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7, 7: 0, 8: 0, 9: 0, 10: 0 };

  // ---- bit buffer ----
  function BitBuf() { this.bits = []; }
  BitBuf.prototype.put = function (val, len) {
    for (var i = len - 1; i >= 0; i--) this.bits.push((val >>> i) & 1);
  };
  BitBuf.prototype.len = function () { return this.bits.length; };

  // ---- Galois field GF(256), poly 0x11D ----
  var EXP = new Array(512), LOG = new Array(256);
  (function () {
    var x = 1;
    for (var i = 0; i < 255; i++) {
      EXP[i] = x; LOG[x] = i;
      x <<= 1;
      if (x & 0x100) x ^= 0x11D;
    }
    for (var j = 255; j < 512; j++) EXP[j] = EXP[j - 255];
  })();
  function gfMul(a, b) { return (a === 0 || b === 0) ? 0 : EXP[LOG[a] + LOG[b]]; }

  function rsGenerator(deg) {
    // Highest-degree-first, monic: g(x) = (x + a^0)(x + a^1)...(x + a^(deg-1))
    var g = [1];
    for (var i = 0; i < deg; i++) {
      var next = new Array(g.length + 1).fill(0);
      for (var j = 0; j < g.length; j++) {
        next[j] ^= gfMul(g[j], EXP[i]);
        next[j + 1] ^= g[j];
      }
      g = next;
    }
    return g.reverse();
  }

  function rsRemainder(data, gen) {
    // Remainder of data(x)*x^deg divided by g(x), straightforward long division.
    var deg = gen.length - 1;
    var a = data.slice();
    for (var i = 0; i < deg; i++) a.push(0);
    for (var k = 0; k < data.length; k++) {
      var f = a[k];
      if (f !== 0) for (var j = 1; j <= deg; j++) a[k + j] ^= gfMul(gen[j], f);
    }
    return a.slice(data.length);
  }

  // ---- data encoding (byte mode) ----
  function utf8bytes(s) {
    var out = [];
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c < 0x80) out.push(c);
      else if (c < 0x800) out.push(0xC0 | (c >> 6), 0x80 | (c & 0x3F));
      else if (c >= 0xD800 && c <= 0xDBFF && i + 1 < s.length) {
        var d = s.charCodeAt(++i);
        var cp = 0x10000 + ((c - 0xD800) << 10) + (d - 0xDC00);
        out.push(0xF0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3F), 0x80 | ((cp >> 6) & 0x3F), 0x80 | (cp & 0x3F));
      } else out.push(0xE0 | (c >> 12), 0x80 | ((c >> 6) & 0x3F), 0x80 | (c & 0x3F));
    }
    return out;
  }

  function pickVersion(byteLen) {
    for (var v = 1; v <= 10; v++) {
      var dataCW = BLOCKS[v][1].reduce(function (a, g) { return a + g[0] * g[1]; }, 0);
      var capBits = dataCW * 8 - 4 - (v <= 9 ? 8 : 16);
      if (Math.floor(capBits / 8) >= byteLen) return v;
    }
    throw new Error("data too long for HP_QR (max version 10, EC-M)");
  }

  function encodeData(bytes, version) {
    var info = BLOCKS[version];
    var totalDataCW = info[1].reduce(function (a, g) { return a + g[0] * g[1]; }, 0);
    var buf = new BitBuf();
    buf.put(4, 4); // byte mode
    buf.put(bytes.length, version <= 9 ? 8 : 16);
    for (var i = 0; i < bytes.length; i++) buf.put(bytes[i], 8);
    var cap = totalDataCW * 8;
    var term = Math.min(4, cap - buf.len());
    buf.put(0, term);
    while (buf.len() % 8 !== 0) buf.put(0, 1);
    var data = [];
    for (var b = 0; b < buf.len(); b += 8) {
      var v = 0;
      for (var k = 0; k < 8; k++) v = (v << 1) | buf.bits[b + k];
      data.push(v);
    }
    var pads = [0xEC, 0x11], pi = 0;
    while (data.length < totalDataCW) data.push(pads[pi++ % 2]);

    // split into blocks, RS-encode, interleave
    var blocks = [], ecBlocks = [], gen = rsGenerator(info[0]);
    var off = 0;
    info[1].forEach(function (g) {
      for (var n = 0; n < g[0]; n++) {
        var d = data.slice(off, off + g[1]); off += g[1];
        blocks.push(d);
        ecBlocks.push(rsRemainder(d, gen));
      }
    });
    var out = [], maxData = Math.max.apply(null, blocks.map(function (b) { return b.length; }));
    for (var i2 = 0; i2 < maxData; i2++)
      blocks.forEach(function (b) { if (i2 < b.length) out.push(b[i2]); });
    for (var j = 0; j < info[0]; j++)
      ecBlocks.forEach(function (e) { out.push(e[j]); });

    var bits = [];
    out.forEach(function (cw) { for (var s = 7; s >= 0; s--) bits.push((cw >> s) & 1); });
    for (var r = 0; r < REM_BITS[version]; r++) bits.push(0);
    return bits;
  }

  // ---- matrix ----
  function blankMatrix(size) {
    var m = [], f = [];
    for (var r = 0; r < size; r++) { m.push(new Array(size).fill(0)); f.push(new Array(size).fill(0)); }
    return { mod: m, func: f, size: size };
  }
  function setMod(M, r, c, dark, isFunc) {
    M.mod[r][c] = dark ? 1 : 0;
    if (isFunc) M.func[r][c] = 1;
  }
  function finder(M, r, c) {
    for (var dr = -1; dr <= 7; dr++) for (var dc = -1; dc <= 7; dc++) {
      var rr = r + dr, cc = c + dc;
      if (rr < 0 || cc < 0 || rr >= M.size || cc >= M.size) continue;
      var dark = (dr >= 0 && dr <= 6 && dc >= 0 && dc <= 6) &&
        (dr === 0 || dr === 6 || dc === 0 || dc === 6 || (dr >= 2 && dr <= 4 && dc >= 2 && dc <= 4));
      setMod(M, rr, cc, dark, true);
    }
  }
  function versionBits(version) {
    // 18-bit BCH(18,6): data = version, generator x^12+x^11+x^10+x^9+x^8+x^5+x^2+1
    var poly = 0x1F25, v = version << 12, bch = v;
    while (bch >= 0x1000) {
      var shift = Math.floor(Math.log2(bch)) - 12;
      bch ^= poly << shift;
    }
    return ((version << 12) | bch) & 0x3FFFF;
  }

  function placeFunctions(M, version) {
    var s = M.size;
    finder(M, 0, 0); finder(M, 0, s - 7); finder(M, s - 7, 0);
    for (var i = 8; i < s - 8; i++) { // timing
      setMod(M, 6, i, i % 2 === 0, true);
      setMod(M, i, 6, i % 2 === 0, true);
    }
    var pos = ALIGN[version], n = pos.length;
    for (var ai = 0; ai < n; ai++) for (var aj = 0; aj < n; aj++) {
      // skip the three grid corners that overlap the finder patterns
      if ((ai === 0 && aj === 0) || (ai === 0 && aj === n - 1) || (ai === n - 1 && aj === 0)) continue;
      var r = pos[ai], c = pos[aj];
      for (var dr = -2; dr <= 2; dr++) for (var dc = -2; dc <= 2; dc++) {
        var dark = Math.max(Math.abs(dr), Math.abs(dc)) !== 1;
        setMod(M, r + dr, c + dc, dark, true);
      }
    }
    setMod(M, s - 8, 8, true, true); // dark module
    if (version >= 7) { // version information blocks (18 bits, two copies)
      var vb = versionBits(version);
      for (var vi = 0; vi < 18; vi++) {
        var bit = (vb >> vi) & 1;
        setMod(M, s - 11 + (vi % 3), Math.floor(vi / 3), bit, true); // bottom-left
        setMod(M, Math.floor(vi / 3), s - 11 + (vi % 3), bit, true); // top-right
      }
    }
    // reserve format info areas
    for (var k = 0; k <= 8; k++) if (k !== 6) { M.func[8][k] = 1; M.func[k][8] = 1; }
    for (var k2 = 0; k2 < 8; k2++) { M.func[8][s - 1 - k2] = 1; M.func[s - 1 - k2][8] = 1; }
  }

  function placeData(M, bits) {
    var s = M.size, i = 0, upward = true;
    for (var col = s - 1; col > 0; col -= 2) {
      if (col === 6) col = 5;
      for (var n = 0; n < s; n++) {
        var r = upward ? s - 1 - n : n;
        for (var c = 0; c < 2; c++) {
          var cc = col - c;
          if (M.func[r][cc]) continue;
          M.mod[r][cc] = i < bits.length && bits[i] ? 1 : 0;
          i++;
        }
      }
      upward = !upward;
    }
  }

  var MASKS = [
    function (r, c) { return (r + c) % 2 === 0; },
    function (r) { return r % 2 === 0; },
    function (r, c) { return c % 3 === 0; },
    function (r, c) { return (r + c) % 3 === 0; },
    function (r, c) { return (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0; },
    function (r, c) { return ((r * c) % 2 + (r * c) % 3) === 0; },
    function (r, c) { return (((r * c) % 2 + (r * c) % 3) % 2) === 0; },
    function (r, c) { return (((r + c) % 2 + (r * c) % 3) % 2) === 0; }
  ];

  function applyMask(M, mask) {
    var s = M.size;
    for (var r = 0; r < s; r++) for (var c = 0; c < s; c++)
      if (!M.func[r][c] && MASKS[mask](r, c)) M.mod[r][c] ^= 1;
  }

  function penalty(M) {
    var s = M.size, score = 0, r, c, k;
    // N1: runs of 5+
    for (r = 0; r < s; r++) {
      var run = 1;
      for (c = 1; c < s; c++) {
        if (M.mod[r][c] === M.mod[r][c - 1]) { run++; if (run === 5) score += 3; else if (run > 5) score++; }
        else run = 1;
      }
    }
    for (c = 0; c < s; c++) {
      var run2 = 1;
      for (r = 1; r < s; r++) {
        if (M.mod[r][c] === M.mod[r - 1][c]) { run2++; if (run2 === 5) score += 3; else if (run2 > 5) score++; }
        else run2 = 1;
      }
    }
    // N2: 2x2 blocks
    for (r = 0; r < s - 1; r++) for (c = 0; c < s - 1; c++) {
      var v = M.mod[r][c];
      if (v === M.mod[r][c + 1] && v === M.mod[r + 1][c] && v === M.mod[r + 1][c + 1]) score += 3;
    }
    // N3: finder-like patterns
    function line(a) {
      for (k = 0; k <= a.length - 11; k++) {
        var p1 = a[k] === 1 && a[k + 1] === 0 && a[k + 2] === 1 && a[k + 3] === 1 && a[k + 4] === 1 &&
          a[k + 5] === 0 && a[k + 6] === 1 && a[k + 7] === 0 && a[k + 8] === 0 && a[k + 9] === 0 && a[k + 10] === 0;
        var p2 = a[k] === 0 && a[k + 1] === 0 && a[k + 2] === 0 && a[k + 3] === 0 && a[k + 4] === 1 &&
          a[k + 5] === 0 && a[k + 6] === 1 && a[k + 7] === 1 && a[k + 8] === 1 && a[k + 9] === 0 && a[k + 10] === 1;
        if (p1 || p2) score += 40;
      }
    }
    for (r = 0; r < s; r++) line(M.mod[r]);
    for (c = 0; c < s; c++) { var col = []; for (r = 0; r < s; r++) col.push(M.mod[r][c]); line(col); }
    // N4: dark ratio
    var dark = 0;
    for (r = 0; r < s; r++) for (c = 0; c < s; c++) dark += M.mod[r][c];
    var pct = dark * 100 / (s * s);
    score += Math.floor(Math.abs(pct - 50) / 5) * 10;
    return score;
  }

  function formatBits(mask) {
    var data = (0 << 3) | mask; // EC level M = 00
    var poly = 0x537, v = data << 10, bch = v;
    while (bch >= 0x400) {
      var shift = Math.floor(Math.log2(bch)) - 10;
      bch ^= poly << shift;
    }
    return (((data << 10) | bch) ^ 0x5412) & 0x7FFF;
  }

  function writeFormat(M, mask) {
    var s = M.size, bits = formatBits(mask), i = 0, r, c;
    // around top-left finder
    var order1 = [];
    for (c = 0; c <= 5; c++) order1.push([8, c]);
    order1.push([8, 7]); order1.push([8, 8]);
    order1.push([7, 8]);
    for (r = 5; r >= 0; r--) order1.push([r, 8]);
    // top-right / bottom-left copies
    var order2 = [];
    for (c = s - 1; c >= s - 8; c--) order2.push([8, c]);
    for (r = s - 7; r < s; r++) order2.push([r, 8]);
    for (i = 0; i < 15; i++) {
      var b = (bits >> (14 - i)) & 1; // first copy: MSB first
      setMod(M, order1[i][0], order1[i][1], b, true);
      var b2 = (bits >> i) & 1; // second copy: LSB first per spec layout
      setMod(M, order2[i][0], order2[i][1], b2, true);
    }
  }

  function encode(text) {
    var bytes = utf8bytes(text);
    var version = pickVersion(bytes.length);
    var bits = encodeData(bytes, version);
    var size = version * 4 + 17;
    var M = blankMatrix(size);
    placeFunctions(M, version);
    placeData(M, bits);
    var best = 0, bestScore = Infinity, snapshots = [];
    for (var m = 0; m < 8; m++) {
      applyMask(M, m);
      writeFormat(M, m);
      var sc = penalty(M);
      snapshots.push(M.mod.map(function (row) { return row.slice(); }));
      if (sc < bestScore) { bestScore = sc; best = m; }
      applyMask(M, m); // unmask
    }
    M.mod = snapshots[best];
    return {
      size: size,
      version: version,
      mask: best,
      dark: function (r, c) { return M.mod[r][c] === 1; },
      modules: M.mod
    };
  }

  return { encode: encode, _version: "1.0.0-hp" };
})();


/* Render a QR code to a PNG data URL via canvas. */
function hpQRDataURL(text, cellSize, margin) {
  var q = HP_QR.encode(text);
  var px = (q.size + margin * 2) * cellSize;
  var cv = document.createElement("canvas");
  cv.width = px; cv.height = px;
  var ctx = cv.getContext("2d");
  ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, px, px);
  ctx.fillStyle = "#000000";
  for (var r = 0; r < q.size; r++)
    for (var c = 0; c < q.size; c++)
      if (q.dark(r, c)) ctx.fillRect((c + margin) * cellSize, (r + margin) * cellSize, cellSize, cellSize);
  return cv.toDataURL("image/png");
}