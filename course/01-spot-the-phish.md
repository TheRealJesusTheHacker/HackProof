# 01 — Spot the Phish: The 60-Second Email Check

## Module Overview

**Level:** Foundations
**Time:** 20 minutes
**Prerequisites:** None.

Phishing is a fake email, or fake site it sends you to, built to harvest your login. The "account locked" message is the classic lure: official-looking, panic-driven, with one link. This module gives you a 60-second check for any email.

**LEARNING OBJECTIVES — After this module you can:**

- Run the five-step, 60-second check on any suspicious email
- Read a sender address and link instead of trusting a display name or logo
- Explain why urgency is a tool used against you
- Apply the one habit: never log in from an email link
- Act correctly after you clicked or entered a password

## Lesson 1: The 60-Second Check

Work these steps in order. Stop as soon as one fails.

1. **Sender address.** Not the display name — the ADDRESS. A message can show "Your Bank Security" while coming from somewhere else. `security@yourbank-secure.com` is not your bank. Look for added words, hyphens, and misspellings.
2. **The greeting.** "Dear Customer" means a mass blast. Your bank knows your name.
3. **Urgency.** "Locked in 24 hours!" Panic is the point — it stops you checking step 1. Treat any deadline as a reason to slow down, not speed up.
4. **The link.** Hover, or press and hold — do not tap. The real domain is right before the first single slash. `yourbank.com.verify-login.ru` is not yourbank.com; that name is only a subdomain, and the site belongs to the ending domain.
5. **The ask.** Banks never ask for passwords, PINs, or full Social Security numbers by email. Ever. If the page asks for one, you have your answer however good it looks.

### Case Breakdown: The Locked Account

**What happened:** Dana gets an email at 7 a.m.: her bank's logo, "Unusual sign-in. Your account will be locked today. Verify your identity." She clicks, lands on a page that looks exactly like her bank, and enters her username, password, and card number. The page says "Verified" and sends her to the real bank site. That login is used that evening from another device.

**Where it could have stopped:** Step 1 — the sender domain had an extra word. Step 4 — the link did not go to her bank. Step 5 — the page asked for a full card number.

**The signal most people miss:** The redirect to the real site. Victims read it as proof the page was genuine. It is the opposite: the fake page has what it needs, and sending you somewhere familiar stops you reporting it.

### What to Do Instead — Checklist

- Close the email. Open your bank's app, or type the address yourself, and sign in there. A real problem will be waiting inside your account.
- If nothing is there, the email was fake. Report it, then delete it.

> **COMMON MISTAKE:** Judging an email by how it looks. Logos, colors, and legal text are copied in seconds — look is the cheapest part to fake. Check address, link, and ask instead.

## Lesson 2: The One Habit

**The one habit: never log in from an email link.** Open the app or type the address yourself. This single habit defeats nearly all phishing because it breaks the chain at the only step the sender controls — where the link takes you. It works even when the email fools you completely.

Use it for shared documents, delivery notices, invoices, and password resets you did not request. If you did request a reset, still check the sender and link first.

### Case Breakdown: The Shared Document

**What happened:** Marcus gets "Invoice_4821.pdf — shared with you" from a name he recognizes. The sign-in page asks for his email password. He enters it. Nothing opens. By morning, his contacts are receiving the same message from his account.

**Where it could have stopped:** At the ask — a document viewer does not need his email password — or with the one habit: opening his files from his own app, where no invoice waited.

**The signal most people miss:** The sender's name was real because that account had been taken over the same way. A familiar name proves nothing about who controls it today.

### If You Clicked

- Clicked but entered nothing? Close the page.
- Entered a password? Change it immediately, from the real app or a typed address — and anywhere you reused it.
- Turn on two-factor authentication (2FA) — app-based, not SMS, if you can.
- Watch the account for a week; report the phish to your bank and reportphishing@apwg.org.

> **COMMON MISTAKE:** Changing the password through the same email link — you may hand the new one to the same fake page.

## Hands-On Exercise

You receive: From "Chase Secure Team" at `alerts@chase-secure-center.com`. Subject: "Action required in 24 hours." Body: "Dear Customer, we detected unusual activity. Verify now."

**Decision point 1:** Do the greeting and deadline decide it? No — warnings, not verdicts.
**Decision point 2:** Which step ends it? Step 1: the domain has extra words and is not the bank's. You do not need the link.
**Decision point 3:** You want certainty. Close the email and open the bank's app yourself.

**Correct path:** Fail it at the sender address, go direct, find no alert, report and delete it. Nothing entered, nothing lost.

## Knowledge Check

**1. An email shows your bank's name and logo. What proves it is real?**
A. The logo and professional design
B. Sender and link matching the bank's real domain, and no request for a password or PIN
C. A footer with a real street address
D. Your first name in the greeting

**2. A link reads `yourbank.com.verify-login.ru`. Where does it go?**
A. Your bank, because yourbank.com appears first
B. A secure page your bank owns
C. A site under the ending domain — not your bank
D. Nowhere; it is a broken link

**3. You entered your password on a page an email sent you to. What first?**
A. Wait to see if anything happens
B. Reply asking if it was real
C. Change the password through the same link
D. Open the real app yourself and change it there — and anywhere you reused it

### Answer Key

**1. B.** Design, footers, and even your name can be copied; domain and ask are what you verify. A fails because appearance is easiest to fake.
**2. C.** Read the ending domain before the first slash. A fails because a familiar name can sit as a subdomain on someone else's site.
**3. D.** Speed matters, but only through a session you opened. C can hand your new password to the same fake page.

## Key Takeaways

- Check the address, not the display name; the link, not the button; the ask, not the design.
- Urgency is a tool used against you. A deadline is a reason to slow down.
- Never log in from an email link. Open the app or type the address yourself.
- A familiar sender name proves nothing.
- If you entered a password, change it from a session you opened, everywhere you reused it, then turn on 2FA.

## Glossary

**Phishing** — A fake message or site designed to steal a login or private information.
**Domain** — The core part of an address or link, such as yourbank.com.
**Subdomain** — Words before a domain; they can make a fake link look familiar while the real domain sits at the end.
**Hover** — Resting a pointer, or pressing and holding on a phone, to preview a link.
**2FA** — Two-factor authentication: a second proof at sign-in beyond your password.
**Display name** — The name shown next to an email; the sender chooses it.

## Further Reading

- FTC — Recognizing phishing: https://consumer.ftc.gov
- Report fraud: https://reportfraud.ftc.gov
- CISA — Phishing guidance: https://www.cisa.gov

## Certification alignment

**Supports:** CompTIA Security+ (SY0-701) Domain 2 — social engineering and phishing recognition.

Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
