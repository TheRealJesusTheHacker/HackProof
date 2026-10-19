"""Finished-certificate generation.

Reproduces, as a standalone print-ready HTML file, the certificate
exam.html renders (same content, same design language: cream stock,
double purple border, Sentinel Safeguard masthead) — with the
VERIFIED badge lit, because by the time this is generated the payload
has passed sign-cert validation and been countersigned.
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
  body{margin:0;background:#0d0718;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;padding:24px}
  .cert-shell{max-width:880px;margin:0 auto;background:#0d0718;border:1px solid #3b2163;border-radius:14px;padding:14px}
  .cert{background:linear-gradient(180deg,#fdfbf7,#f5efe4);color:#1c1530;border-radius:8px;
    padding:34px 26px;text-align:center;position:relative;overflow:hidden;border:10px double #6d28d9}
  .cert::before{content:"";position:absolute;inset:14px;border:1px solid #a855f7aa;pointer-events:none}
  .cert .org{font-size:13px;letter-spacing:.34em;color:#6d28d9;font-weight:800}
  .cert h3{font-size:30px;margin:10px 0 2px;color:#1c1530;letter-spacing:.02em}
  .cert .sub{font-size:14px;color:#5b5470;margin:0 0 18px}
  .cert .label{font-size:12px;letter-spacing:.28em;color:#8a7fa8;text-transform:uppercase;margin:14px 0 2px}
  .cert .name{font-size:34px;font-weight:800;color:#1c1530;font-family:Georgia,"Times New Roman",serif;margin:2px 0 6px;word-wrap:break-word}
  .cert .rule{width:60%%;margin:6px auto;border:0;border-top:2px solid #6d28d955}
  .cert .details{font-size:15px;color:#3d3654;margin:8px 0}
  .cert .details b{color:#1c1530}
  .cert .cid{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:15px;letter-spacing:.1em;color:#4c1d95;font-weight:700}
  .cert .sealrow{display:flex;justify-content:space-between;align-items:flex-end;margin:26px 6px 0;text-align:left}
  .cert .sig{font-size:13px;color:#5b5470}
  .cert .sig .line{border-top:1px solid #6d28d9;margin-top:26px;padding-top:4px;font-size:12px}
  .cert .badge{display:inline-block;background:#059669;color:#fff;font-size:11px;font-weight:800;
    letter-spacing:.14em;border-radius:99px;padding:6px 14px;margin-top:10px}
  .verify-note{max-width:880px;margin:14px auto 0;color:#9d8fb8;font-size:13px;text-align:center;line-height:1.6}
  .verify-note b{color:#d8b4fe}
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
