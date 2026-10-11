# Phishing — Don't Take the Bait

## What it is

**Phishing** is a fake message — email, text, or DM — designed to look like
it's from someone you trust (your bank, a delivery company, your boss, a
government agency) so you'll click a link, open an attachment, or hand over
login details or money. Texts are sometimes called **smishing** (SMS
phishing); the playbook is identical. The message creates pressure — a
locked account, a missed delivery, a limited-time problem — because rushed
people don't double-check.

## Why it matters

Phishing is how most account takeovers and a huge share of scams actually
start. The attacker doesn't need to break any security software — they just
need one tired person to click at the wrong moment. Nobody is "too smart"
for it: these messages are mass-produced, professionally designed, and
timed to catch you off guard (Monday-morning inbox, holiday shipping
season). Your defense isn't sharper eyes — it's a habit: verify before you
click, every time.

## How the attack really works

**Example 1 — The fake delivery text.** "USPS: Your package could not be
delivered. Update your address here: [link]." The link goes to a page
dressed up like USPS that asks for your address "to reschedule" — then asks
for a small "redelivery fee" and your full card details. There is no
package. The site exists only to harvest your card number. These spike
around holidays when everyone's expecting packages.

**Example 2 — The locked-account email.** "Your Apple ID has been locked
due to suspicious activity. Verify within 24 hours or your account will be
permanently disabled: [link]." The sender address is something like
`apple-support@notice-appleid.com` — close enough at a glance, but not
Apple. The link leads to a pixel-perfect copy of Apple's sign-in page.
You enter your Apple ID and password; the page shows an error. The attacker
now has your credentials and immediately tries them on your email too.

**Example 3 — The invoice attachment.** An email that looks like it's from
a vendor or coworker: "Please review the attached invoice." The attachment
is named something like `Invoice-1042.pdf` — but it's actually an HTML file
or a disguised program that opens a fake login page, or installs malware
when opened. Businesses lose real money to fake-invoice emails that
redirect a payment to the attacker's account.

**Example 4 — The QR code switch.** A flyer, parking meter sticker, or
emailed "verify your account" message with a QR code. Scanning it opens a
fake login page in your browser. Same scam, new wrapper — your phone can't
tell you where a QR code goes until you've already opened it.

## Action checklist (do these today)

- [ ] **Build the verify-before-you-click habit.** Got a message about your
      bank, a delivery, or an account? Don't click the link. Open the real
      app on your phone or type the company's real website address yourself
      and check there. If there's really a problem, you'll see it when you
      sign in directly.
- [ ] **Check the sender, for real.** On email, expand the "From" field and
      read the full address — `support@yourbank.com` vs
      `support@yourbank-secure-alert.com` are not the same. On texts,
      remember: banks and delivery companies text from short codes or
      verified sender IDs, not random 10-digit numbers.
- [ ] **Hover before you tap (on a computer).** Hover your mouse over a
      link and look at the address shown in the corner. If the text says
      "chase.com" but the real address is `chase-secure-login.ru`, it's
      fake. On a phone, long-press the link to preview where it goes.
- [ ] **Turn on spam/phishing filters** in your email and messaging apps if
      they aren't on — and use "Report phishing" / "Report junk" when one
      slips through. On texts, most US carriers let you forward spam to
      **7726** (spells SPAM) to report it.
- [ ] **Make sure MFA is on** for your email and bank (see Module 1) — so a
      stolen password alone isn't enough to get in.
- [ ] **Tell the people around you.** Forward one real example to your
      family group chat and point out what gave it away. The people
      attackers love most are the ones nobody warned.

## Red flags

- **Urgency or threats:** "Act within 24 hours," "your account will be
  closed," "final notice." Real companies don't threaten you into clicking.
- **Too-good or too-scary to be true:** surprise refunds, prizes you never
  entered, legal threats out of nowhere.
- **Generic greetings:** "Dear Customer" instead of your name (your real
  bank knows your name).
- **Odd sender addresses** or display names that don't match the address
  underneath.
- **Attachments you didn't ask for** — especially invoices, "shipping
  labels," or anything ending in `.html`, `.zip`, or double extensions like
  `document.pdf.exe`.
- **Requests for gift cards, wire transfers, or crypto** to "fix" a
  problem. Always a scam. Every time.

## What to do if you clicked

Don't panic — act fast and in this order:

1. **If you entered a username/password:** change that password *right
   now*, from the real site (type the address yourself), and turn on MFA
   if it isn't on. Then change it anywhere else you reused it.
2. **If you entered card or bank details:** call your bank or card company
   immediately using the number on the back of your card — not any number
   from the message. Ask about freezing the card or watching for fraud.
3. **If you downloaded or opened an attachment:** disconnect from WiFi,
   don't enter passwords or bank info on that device until it's checked,
   and run a full scan with reputable antivirus/antimalware software. If
   anything feels off after that, have a professional look at it.
4. **If you entered a Social Security number or ID details:** consider
   placing a fraud alert or credit freeze with the major credit bureaus —
   it's free and you can lift it anytime.
5. **Report it:** mark the message as phishing in your email app, forward
   spam texts to 7726, and report it to the company being impersonated
   (most big companies have a phishing-report address like
   phishing@companyname.com).
6. **Watch the account** for strange activity over the next few weeks.

## Quiz

**Q1.** You get a text: "Your package couldn't be delivered, update your
address here: [link]." You're not expecting a package. What's the safest
move?
A) Click the link — maybe it's a surprise gift
B) Reply STOP to opt out
C) Ignore it, and if you're curious, check tracking in the delivery
   company's real app or website by typing the address yourself
D) Forward it to five friends to warn them, then click

**Q2.** An email says it's from your bank and the link text reads
"bankofamerica.com", but hovering shows the real address is
`bankofarnerica-login.com`. What does that tell you?
A) Nothing — the link text is what matters
B) It's legitimate; banks use alternate domains
C) It's phishing — the real destination doesn't match the claimed one
D) Your mouse is broken

**Q3.** You realized you just typed your email password into a fake login
page. What's the FIRST thing to do?
A) Email the scammer and demand they delete it
B) Change your email password immediately on the real site, then enable MFA
C) Wait and see if anything bad happens
D) Delete the phishing email so you don't click it again

---

### Answer key

**Q1 — C.** Unsolicited delivery texts with links are one of the most
common phishing lures. Never click; verify through the real app or site.
(Replying STOP just confirms your number is live.)

**Q2 — C.** Attackers control the visible link text — only the real
destination address tells the truth. Lookalike domains (`arnerica` vs
`america`) are a classic tell.

**Q3 — B.** Speed matters: change the password on the real site before the
attacker uses it, and MFA means the stolen password alone won't be enough
next time.
