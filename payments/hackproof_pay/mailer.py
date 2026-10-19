"""Email delivery (stdlib smtplib) + the two product emails.

When SMTP is not configured, delivery degrades honestly: no email is
sent, the buyer claims their key through the order-status endpoint,
and every skipped send is logged loudly. The service never pretends an
email went out when it didn't.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

log = logging.getLogger("hackproof_pay.mailer")


class Mailer:
    def __init__(self, smtp_cfg, support_email):
        self._cfg = smtp_cfg or {}
        self._support = support_email

    @property
    def configured(self):
        return bool(self._cfg.get("host"))

    def send(self, to, subject, body, attachments=()):
        """attachments: [(filename, bytes, maintype, subtype)].
        Returns True when the message was handed to the SMTP server."""
        if not self.configured:
            log.warning(
                "SMTP NOT CONFIGURED — email to %s not sent "
                "(subject: %s). Buyer falls back to the claim "
                "endpoint.", to, subject)
            return False
        msg = EmailMessage()
        frm_name = self._cfg.get("from_name") or "Sentinel Safeguard"
        frm_addr = self._cfg.get("from_address") or self._support
        msg["From"] = "%s <%s>" % (frm_name, frm_addr)
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        for filename, data, maintype, subtype in attachments:
            msg.add_attachment(data, maintype=maintype, subtype=subtype,
                               filename=filename)
        host = self._cfg["host"]
        port = int(self._cfg.get("port") or 587)
        security = (self._cfg.get("security") or "starttls").lower()
        try:
            if security == "ssl":
                server = smtplib.SMTP_SSL(host, port, timeout=30)
            else:
                server = smtplib.SMTP(host, port, timeout=30)
            with server:
                if security == "starttls":
                    server.starttls()
                if self._cfg.get("username"):
                    server.login(self._cfg["username"],
                                 self._cfg.get("password") or "")
                server.send_message(msg)
        except Exception as exc:
            log.error("SMTP send to %s FAILED: %s", to, exc)
            return False
        log.info("email sent to %s (subject: %s)", to, subject)
        return True


def license_email_body(cfg_values, order, license_key, claim_hint):
    """The delivery email for a premium license key.

    Owner's framing, verbatim in spirit: THE KEY IS THE ACCOUNT.
    There is no login and no password — whoever holds the key holds
    the premium access.
    """
    days = int(cfg_values["license_days"])
    lines = [
        "Hello,",
        "",
        "Thank you for purchasing HackProof Premium. Your Bitcoin "
        "payment has been detected and confirmed, and your license "
        "key has been generated for you automatically.",
        "",
        "YOUR LICENSE KEY:",
        "",
        license_key,
        "",
        "THIS KEY IS YOUR ACCOUNT.",
        "",
        "HackProof has no usernames and no passwords. This key is "
        "your account and your only credential — it is what unlocks "
        "premium on any device you use it on.",
        "",
        "Save it somewhere safe: a password manager, a printed copy "
        "in a drawer, anywhere you would keep something you cannot "
        "replace. Whoever holds this key holds the premium access — "
        "treat it like the key to your house, because for HackProof, "
        "it is one.",
        "",
        "HOW TO REDEEM:",
        "1. Open HackProof: %s" % cfg_values["site_url"],
        "2. Choose \"Enter license key\" and paste the key above.",
        "3. Premium unlocks immediately — all scenarios, all "
        "field-manual modules, and the final exam.",
        "",
        "Your license lasts %d days from today. Expiry is checked "
        "against your device's clock, so keep your clock accurate."
        % days,
        "",
        "Lost this email? %s" % claim_hint,
        "Questions or a key that doesn't work: %s"
        % cfg_values["support_email"],
        "",
        "— Sentinel Safeguard LLC",
        "HackProof · Kansas City, MO",
    ]
    return "\n".join(lines) + "\n"


def certificate_email_body(cfg_values, payload, countersigned_code):
    """The delivery email for the finished certificate."""
    lines = [
        "Hello %s," % payload.get("name", ""),
        "",
        "Congratulations — you passed the HackProof final exam, and "
        "your certificate has been issued and countersigned "
        "automatically.",
        "",
        "You have earned the Sentinel Safeguard Certificate of "
        "Cyber Security Awareness Course Completion.",
        "",
        "Final exam score: %s%% (%s/90)" % (payload.get("pct"),
                                            payload.get("score")),
        "Certificate ID: %s" % payload.get("cert_id", ""),
        "Date: %s" % payload.get("date", ""),
        "",
        "Your finished certificate is attached to this email "
        "(print-ready HTML — open it and print, or save as PDF).",
        "",
        "VERIFICATION:",
        "Anyone can check your certificate at the public verify "
        "page:",
        cfg_values["verify_url"],
        "",
        "Your countersigned verification code is:",
        "",
        countersigned_code,
        "",
        "You can also paste that code into the exam page to light "
        "up the verified seal on your certificate there. Keep the "
        "code with the certificate — it is the proof the seal is "
        "genuine.",
        "",
        "Questions: %s" % cfg_values["support_email"],
        "",
        "— Sentinel Safeguard LLC",
        "HackProof · Kansas City, MO",
    ]
    return "\n".join(lines) + "\n"
