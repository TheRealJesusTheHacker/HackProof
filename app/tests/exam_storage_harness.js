"use strict";
/* Behavioral harness for exam.html's license-storage opt-in
   (sweep #3, 2026-10-21). Run by app/tests/test_exam_storage.py
   under Node; not shipped (app/ never enters the bundle).

   Loads the REAL shared.js + the exam page's real scripts into a
   vm with a stub DOM and a recording localStorage, then drives
   the exam gate exactly as a student would:
     1. no opt-in  -> Begin stores NOTHING (key + name stay
        memory-only) and the exam still starts;
     2. opt-in     -> Begin stores the key (and name);
     3. a previously stored key prefills the gate with the
        remember box checked; unchecking and beginning removes
        the stored copy;
     4. a localStorage that throws on every access still gets a
        working gate (session-only), never a blank page.
   License.verifyLicense is stubbed AFTER the real shared.js
   loads (the crypto itself is pinned by the Python suites);
   everything else — gate rendering, the storage writes, the
   session key's reuse for certificate delivery — is page code. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");
const sharedJs = fs.readFileSync(path.join(ROOT, "shared.js"), "utf8");
const examHtml = fs.readFileSync(path.join(ROOT, "exam.html"), "utf8");
const scripts = [...examHtml.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .map((m) => m[1]);
// scripts[0] = question bank, scripts[1] = the exam app.
// (The src= loader tag and the copy-protection snippet are not
// inline <script> bodies and are not needed here.)
if (scripts.length < 2) throw new Error("exam scripts not found");

class El {
  constructor() {
    this.value = ""; this.checked = false; this.textContent = "";
    this.disabled = false; this.style = {}; this.dataset = {};
    this.classList = { add() {}, remove() {}, contains: () => false };
    this.children = [];
  }
  set innerHTML(v) { this._html = v; }
  get innerHTML() { return this._html || ""; }
  querySelectorAll() { return []; }
  querySelector() { return new El(); }
  appendChild(c) { this.children.push(c); return c; }
  addEventListener() {}
  select() {} remove() {} focus() {} click() {
    if (this.onclick) return this.onclick();
  }
}

function makeWorld(storageImpl) {
  const registry = new Map();
  const el = (key) => {
    if (!registry.has(key)) registry.set(key, new El());
    return registry.get(key);
  };
  const sandbox = {
    console, setTimeout, clearTimeout,
    performance: { now: () => 1000 },
    crypto: require("node:crypto").webcrypto,
    TextEncoder, TextDecoder, atob, btoa,
    localStorage: storageImpl,
    document: {
      querySelector: (s) => el(s),
      querySelectorAll: () => [],
      getElementById: (id) => el("#" + id),
      createElement: () => new El(),
      addEventListener() {},
      hidden: false,
    },
    navigator: {},
    location: { pathname: "/exam.html" },
    scrollTo() {},
    confirm: () => true,
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  sandbox.window.addEventListener = () => {};
  sandbox.addEventListener = () => {};
  vm.createContext(sandbox);
  vm.runInContext(sharedJs, sandbox, { filename: "shared.js" });
  // The stub seam: genuine-key crypto is pinned elsewhere; the
  // gate's storage behavior is what is under test.
  vm.runInContext(
    "License.verifyLicense = (str) => Promise.resolve({" +
    "id: 'LIC-TEST', tier: 'premium', expiry: 4102444800," +
    "S: new Uint8Array(32)});",
    sandbox, { filename: "stub.js" });
  vm.runInContext(scripts[0], sandbox, { filename: "questions.js" });
  vm.runInContext(scripts[1], sandbox, { filename: "exam-app.js" });
  return { sandbox, el };
}

function recordingStorage(initial, throws) {
  const map = new Map(Object.entries(initial || {}));
  const writes = [];
  const guard = () => { if (throws) throw new Error("storage denied"); };
  return {
    map, writes,
    getItem(k) { guard(); return map.has(k) ? map.get(k) : null; },
    setItem(k, v) { guard(); writes.push(["set", k]); map.set(k, String(v)); },
    removeItem(k) { guard(); writes.push(["remove", k]); map.delete(k); },
  };
}

const flush = () => new Promise((r) => setTimeout(r, 10));
let failures = 0;
function check(name, cond) {
  console.log((cond ? "ok" : "FAIL") + " - " + name);
  if (!cond) failures++;
}

async function begin(world, { name, lic, remember }) {
  const { el } = world;
  el("#gate-name").value = name;
  el("#gate-lic").value = lic;
  el("#gate-remember").checked = remember;
  await el("#gate-go").onclick();
  await flush();
}

(async () => {
  const LIC_KEY = "hackproof_license_v1";
  const NAME_KEY = "hackproof_exam_name";

  // Gate renders the opt-in checkbox (unchecked with no saved key).
  {
    const w = makeWorld(recordingStorage());
    check("gate renders remember checkbox",
          w.el("#app").innerHTML.includes('id="gate-remember"'));
    check("checkbox unchecked when nothing saved",
          !/id="gate-remember" checked/.test(w.el("#app").innerHTML));
  }

  // 1. No opt-in: nothing is stored; the exam still starts.
  {
    const store = recordingStorage();
    const w = makeWorld(store);
    await begin(w, { name: "Test Student", lic: "KEY-ONE",
                     remember: false });
    check("no-opt-in: license key NOT stored",
          !store.map.has(LIC_KEY));
    check("no-opt-in: name NOT stored", !store.map.has(NAME_KEY));
    check("no-opt-in: no setItem writes at all",
          !store.writes.some(([op]) => op === "set"));
    check("no-opt-in: exam started",
          w.el("#app").innerHTML.includes("QUESTION 1 / 90"));
  }

  // 2. Opt-in: the key (and name) are stored.
  {
    const store = recordingStorage();
    const w = makeWorld(store);
    await begin(w, { name: "Test Student", lic: "KEY-TWO",
                     remember: true });
    check("opt-in: license key stored",
          store.map.get(LIC_KEY) === "KEY-TWO");
    check("opt-in: name stored",
          store.map.get(NAME_KEY) === "Test Student");
    check("opt-in: exam started",
          w.el("#app").innerHTML.includes("QUESTION 1 / 90"));
  }

  // 3. Previously stored key: prefilled + box pre-checked;
  //    unchecking takes the stored copy back.
  {
    const store = recordingStorage({ [LIC_KEY]: "KEY-OLD",
                                     [NAME_KEY]: "Old Name" });
    const w = makeWorld(store);
    check("saved key prefilled at the gate",
          w.el("#app").innerHTML.includes("KEY-OLD"));
    check("remember pre-checked for a saved key",
          /id="gate-remember" checked/.test(w.el("#app").innerHTML));
    await begin(w, { name: "Old Name", lic: "KEY-OLD",
                     remember: false });
    check("uncheck: stored license key removed",
          !store.map.has(LIC_KEY));
    check("uncheck: stored name removed", !store.map.has(NAME_KEY));
  }

  // 4. Storage throws everywhere: gate renders, Begin works.
  {
    const store = recordingStorage(null, true);
    const w = makeWorld(store);
    check("denied storage: gate still renders",
          w.el("#app").innerHTML.includes('id="gate-go"'));
    await begin(w, { name: "Test Student", lic: "KEY-X",
                     remember: true });
    check("denied storage: exam still starts",
          w.el("#app").innerHTML.includes("QUESTION 1 / 90"));
  }

  if (failures) { console.log(failures + " FAILURES"); process.exit(1); }
  console.log("exam storage harness: all scenarios pass");
})().catch((e) => { console.error(e); process.exit(1); });
