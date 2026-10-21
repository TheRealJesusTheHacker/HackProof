"""Finished-certificate generation.

Reproduces, as a standalone print-ready HTML file, the certificate
exam.html renders (same content, same design language: cream stock,
double border, Sentinel Safeguard masthead) — with the VERIFIED badge
lit, because by the time this is generated the payload has passed
sign-cert validation and been countersigned.

Palette (sweep #3, 2026-10-21 — the parked contrast item, decided):
this certificate now wears the same academy palette the app
certificate proved in app-v1.0.4 (the bundler's BRAND_MAP retint of
the exam page's certificate), instead of the website's house-green
tokens it previously copied. The mapping is the BRAND_MAP one,
applied to the values this template carries:

  house #14532d (org line, cert ID, badge fill, frame)
        -> academy DEEP #115635 — 8.44:1 on the cream stock
  house #2f4536 (small print: sub, labels, details, signature)
        -> academy small-print tone #0c3723 — 12.81:1 on the stock
  house #0c130d (headline / name / bold text) -> #0a100c
  house #1e7a3c (inner hairline, decorative only) -> #167547
  page ground #060a07 -> #050807, hairline #1e3323 -> #1e2b21
  verify note #9db3a4 -> #90a894 (7.87:1 on the page ground)

Certificate gold (#c9a227) appears exactly once: the verify note's
emphasis, on the near-black page ground, where it measures 8.31:1.
Gold NEVER carries text on the cream stock — there it measures
only 2.34:1. Every text/background pairing in this file measures
>= 4.5:1 against the darker cream stop (#f5efe4) as the worst
case; the payments suite recomputes every pairing from the
rendered file and pins that. No purple anywhere. The cream stock
itself (#fdfbf7 -> #f5efe4) is unchanged — it is the paper, not a
brand token.
"""

from __future__ import annotations

import html

CERT_ACHIEVEMENT = ("Sentinel Safeguard Certificate of Cyber Security "
                    "Awareness Course Completion")

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>%(title)s</title>
<style>
  body{margin:0;background:#050807;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;padding:24px}
  .cert-shell{max-width:880px;margin:0 auto;background:#050807;border:1px solid #1e2b21;border-radius:14px;padding:14px}
  .cert{background:linear-gradient(180deg,#fdfbf7,#f5efe4);color:#0a100c;border-radius:8px;
    padding:34px 26px;text-align:center;position:relative;overflow:hidden;border:10px double #115635}
  .cert::before{content:"";position:absolute;inset:14px;border:1px solid #167547aa;pointer-events:none}
  .cert .org{font-size:13px;letter-spacing:.34em;color:#115635;font-weight:800}
  .cert h3{font-size:30px;margin:10px 0 2px;color:#0a100c;letter-spacing:.02em}
  .cert .sub{font-size:14px;color:#0c3723;margin:0 0 18px}
  .cert .label{font-size:12px;letter-spacing:.28em;color:#0c3723;text-transform:uppercase;margin:14px 0 2px}
  .cert .name{font-size:34px;font-weight:800;color:#0a100c;font-family:Georgia,"Times New Roman",serif;margin:2px 0 6px;word-wrap:break-word}
  .cert .rule{width:60%%;margin:6px auto;border:0;border-top:2px solid #11563555}
  .cert .details{font-size:15px;color:#0c3723;margin:8px 0}
  .cert .details b{color:#0a100c}
  .cert .cid{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:15px;letter-spacing:.1em;color:#115635;font-weight:700}
  .cert .sealrow{display:flex;justify-content:space-between;align-items:flex-end;margin:26px 6px 0;text-align:left}
  .cert .sig{font-size:13px;color:#0c3723}
  .cert .sig .line{border-top:1px solid #115635;margin-top:26px;padding-top:4px;font-size:12px}
  .cert .badge{display:inline-block;background:#115635;color:#fff;font-size:11px;font-weight:800;
    letter-spacing:.14em;border-radius:99px;padding:6px 14px;margin-top:10px}
  .verify-note{max-width:880px;margin:14px auto 0;color:#90a894;font-size:13px;text-align:center;line-height:1.6}
  .verify-note b{color:#c9a227}
  @media print{ @page{size:letter;margin:0.45in} body{background:#fff;padding:0} .verify-note{display:none} }
</style>
</head>
<body>
<div class="cert-shell"><div class="cert">
  <div class="org">SENTINEL SAFEGUARD LLC</div>
  <h3>Certificate of Completion</h3>
  <p class="sub">Cyber Security Awareness Course</p>
  <div class="label">This certifies that</div>
  <div class="name">%(name)s</div>
  <hr class="rule">
  <div class="details">has successfully completed the <b>HackProof Cyber Security Awareness Course</b><br>
  Final exam score: <b>%(pct)s%%</b> (%(score)s/90) &middot; %(date)s</div>
  <div class="label">Certificate ID</div>
  <div class="cid">%(cert_id)s</div>
  <div class="sealrow"><div class="sig"><div class="line">JesusTheHacker &middot; Sentinel Safeguard LLC</div></div>
  <div class="badge">&#10003; VERIFIED</div></div>
</div></div>
<p class="verify-note">Verify this certificate at <b>%(verify_url)s</b> using the countersigned
verification code from the delivery email. Certificate ID: <b>%(cert_id)s</b></p>
</body>
</html>
"""


def render_certificate_html(payload, verify_url) -> str:
    """payload: the validated exam payload (name, score, pct, date,
    cert_id). All user-shaped strings are HTML-escaped."""
    esc = lambda v: html.escape(str(v), quote=True)
    return _TEMPLATE % {
        "title": CERT_ACHIEVEMENT,
        "name": esc(payload.get("name", "")),
        "pct": esc(payload.get("pct", "")),
        "score": esc(payload.get("score", "")),
        "date": esc(payload.get("date", "")),
        "cert_id": esc(payload.get("cert_id", "")),
        "verify_url": esc(verify_url),
    }


def certificate_filename(payload) -> str:
    cid = str(payload.get("cert_id") or "certificate").replace("/", "-")
    return "HackProof-Certificate-%s.html" % cid
