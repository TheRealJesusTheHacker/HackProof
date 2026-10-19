# Phishing — Don't Take the Bait

## Module overview

**Level:** Foundations
**Estimated time:** 45–55 minutes
**Prerequisites:** None, but Module 1 (Passwords & MFA) helps — MFA is what limits the damage if a password is stolen.

### Learning objectives

After this module you can:

- Identify pressure tactics and sender, link, and attachment warning signs in a phishing message.
- Verify a suspicious message by going to the real app or website yourself, without using the link or number provided.
- Check a sender address, link destination, and attachment type before you act.
- Apply the same verification habit to texts, QR codes, and invoice messages, not just email.
- Execute the first response steps in order after entering credentials or payment details, or opening an attachment.

## Lesson 1 — Anatomy of a phishing message

**Phishing** is a fake message — email, text, or direct message — designed to look like it is from someone you trust: your bank, a delivery company, your boss, or a government agency, so you will click a link, open an attachment, or hand over login details or money. Texts are sometimes called **smishing** (SMS phishing). The playbook is identical.

The message almost always creates pressure: a locked account, a missed delivery, an unrecognized charge, a deadline today. That is deliberate — rushed people do not double-check. These messages are mass-produced, professionally designed, and timed to catch you off guard.

Your defense is not sharper eyes. Even careful people miss a well-made fake. Your defense is a habit: verify before you click, through a channel you choose.

### Case breakdown

**The locked-account email — step by step**

1. An email warns: "Your Apple ID has been locked. Verify within 24 hours or it will be permanently disabled," with a sign-in button.
2. The sender shows as "Apple Support," but the full address is `apple-support@notice-appleid.com` — close at a glance, not Apple.
3. The button leads to a pixel-perfect copy of Apple's sign-in page on a different domain.
4. You enter your ID and password. The page shows a vague error and never loads your account.
5. The attacker tries those credentials on your email immediately, betting on reuse.

**Where it could have been stopped:** Step 1. Close the email and check your account via Settings or Apple's real address, typed by you. A real lock will still be there. The deadline was the weapon.

**The signal most people miss:** The threat itself. Real companies let you sign in and resolve a problem; they do not make one link in one email your only chance to save the account.

**Red-flag scan — run it on every unexpected message**

- Urgency or threats: "act within 24 hours," "account will be closed," "final notice."
- A surprise you did not initiate: a refund, prize, charge, delivery, or invoice you were not expecting.
- A generic greeting — "Dear Customer" — from a company that normally uses your name.
- Payment by gift cards, wire transfer, or crypto to "fix" a problem. Always a scam.
- A request for secrecy or to bypass a normal approval step.

> **Common mistake:** Judging a message by how professional it looks. Logos and formatting are cheap to copy; design proves nothing about who sent it.

## Lesson 2 — Check the sender, the link, and the attachment for real

Attackers control what a message *appears* to say. They do not control the real sender domain, real link destination, or what a file actually is — if you know where to look.

**Sender:** Expand the From field and read the full address, not just the display name. `support@yourbank.com` and `support@yourbank-secure-alert.com` are different senders. On texts, distrust random 10-digit numbers claiming to be a bank or delivery company, which normally use short codes or verified IDs.

**Link:** Hover over a link and read the address shown in the corner. If the text says "chase.com" but the destination is `chase-secure-login.ru`, it is fake. On a phone, long-press to preview without opening. Watch for lookalike spellings — one swapped letter is enough.

**Attachment:** Treat unsolicited attachments as hostile, especially invoices, "shipping labels," and files ending in `.html`, `.zip`, or with double extensions like `document.pdf.exe`. A real PDF does not ask you to sign in.

### Case breakdown

**The invoice that was not an invoice — step by step**

1. A small office gets an email that looks like a regular vendor's: "Please review the attached invoice."
2. The attachment, `Invoice-1042.pdf`, is actually an HTML file. Opening it shows a convincing Microsoft sign-in page.
3. An employee enters work credentials. The page stalls.
4. The attacker enters the real mailbox, finds an ongoing payment thread, and replies inside it with "updated" bank details.
5. The next real payment goes to the attacker. The vendor never sent the first email.

**Where it could have been stopped:** Step 2. Checking the file type — and asking why a PDF needs a sign-in — breaks the chain before any password is entered.

**The signal most people miss:** The payment-change request inside a familiar thread. Familiar context feels like proof. It is not — a compromised mailbox lets an attacker reply inside real conversations.

**Verification procedure — the 30-second check**

1. Stop. Do not click, open, reply, or call any number in the message.
2. Read the full sender address and hover or long-press the link to see the real destination.
3. Open the company's real app, or type its real address yourself, and sign in there. A real problem will be waiting for you.
4. If it claims to be someone you know, contact them on a number you already trust — do not reply to this message.
5. If it fails any check, report it as phishing or junk and delete it. Forward US spam texts to **7726** (SPAM).

> **Common mistake:** Replying STOP or clicking "unsubscribe" in a suspicious text or email. In a legitimate marketing message that works. In a phishing message it tells the sender they reached a real, responsive target.

## Lesson 3 — Beyond email: smishing, QR codes, and delivery lures

Phishing moved wherever your attention moved: texts, social messages, and QR codes. The story changes; the request is the same — click, scan, sign in, or pay now.

Texts work because you read them quickly and your phone shows less sender detail. Delivery lures spike around holidays, when a "problem with your delivery" sounds plausible to almost everyone.

QR codes add a blind spot: your phone cannot tell you where a code goes until you scan it. Treat any code on a meter, flyer, or email like an unknown link — because that is what it is.

### Case breakdown

**The fake delivery text — step by step**

1. A text: "USPS: Your package could not be delivered. Update your address here: [link]."
2. The link opens a page styled like the postal service asking for your address "to reschedule."
3. It then asks for a small "redelivery fee" — and your full card details.
4. There is no package. The page exists only to harvest card numbers; the small fee makes it feel low-risk.

**Where it could have been stopped:** Step 1. You were not expecting a package, and real delivery problems are visible when you track the shipment in the carrier's real app or on its real site, typed by you.

**The signal most people miss:** The payment request. The moment a "delivery problem" becomes a card form, it is a harvest page.

**Channel checklist**

- [ ] Delivery: track only in the carrier's app or site you open yourself. Never pay a redelivery fee from a text link.
- [ ] QR codes: after scanning, read the address your phone shows *before* it opens or before you enter anything. If it is a sign-in or payment page you did not expect, close it.
- [ ] Social media: a friend suddenly sending investment or prize messages is usually a compromised account. Verify off the platform.
- [ ] Work messages: an urgent payment, bank-detail change, or gift-card request gets confirmed by voice on a known number, every time — see Module 3.
- [ ] Turn on spam and phishing filters in your email and messaging apps, and use "Report phishing" / "Report junk" when one slips through.

> **Common mistake:** Assuming a QR code is safe because it is printed on something physical, like a meter sticker or a posted flyer. Anyone can place a sticker over a real code. The destination is what matters, not the paper.

## Lesson 4 — If you clicked: the first ten minutes

Clicking is not the end. Attackers need what you do next — enter credentials or payment details, install something, or do nothing while they use what you gave them. Fast, ordered action limits the damage. Do not panic, and do not hide it: at work, quick reporting is what security teams want.

### Case breakdown

**The click that stayed small — step by step**

1. Priya taps a shipping link at lunch and enters her email password on a page that looks right. The page errors out.
2. Within a minute she notices a strange domain in the address bar and closes the page.
3. From the real email app, she changes her email password immediately and confirms MFA is on.
4. She reused that password on one shopping site, so she changes it there too. She entered no card details, so she simply notes the event with her bank.
5. She forwards the text to 7726 and warns her household chat with a screenshot of what fooled her.

**Where it could have been stopped:** Entry was the mistake, but Step 3 is why nothing was lost — the stolen password stopped working before the attacker used it, and MFA would have blocked a sign-in in the gap.

**The signal most people miss:** The fake page's error. Real sign-in pages do not take your password and then simply fail. An error right after entering credentials is itself an alarm.

**Response checklist — in order**

1. **Entered a username or password?** Change it right now from the real site (type the address yourself), turn on MFA, and change it anywhere you reused it. Check email forwarding rules afterward (Module 1).
2. **Entered card or bank details?** Call your bank immediately using the number on the back of your card — never a number from the message. Ask about replacing the card.
3. **Opened an attachment?** Disconnect from Wi-Fi, do not enter passwords on that device until it is checked, and run a full antivirus scan. If anything still feels off, have a professional examine it.
4. **Entered a Social Security number or ID details?** Consider a fraud alert or free credit freeze with the major bureaus.
5. **Report it:** mark it as phishing, forward spam texts to 7726, and notify the impersonated company.
6. **Watch the accounts** for strange activity over the next few weeks.

> **Common mistake:** Waiting to see if anything bad happens. Attackers use stolen credentials within minutes. A password changed in the first ten minutes is often a non-event; the same change next week can be a recovery project.

## Hands-on exercise

**Scenario:** Monday, 9:12 a.m. An email from "IT Helpdesk" — "Password expires today" — says your work password expires at noon and links to a reset page. Expirations do happen at your job.

**Decision point 1 — First move.**
A) Click the link quickly so you are not locked out at noon.
B) Read the full sender address and hover the link before doing anything.
C) Reply asking if the email is real.
D) Forward it to coworkers to ask if they got one.

**Correct path: B.** The sender domain and real link destination tell you more than the subject ever will. Replying (**C**) answers the suspect sender, and forwarding (**D**) spreads a live phishing link.

**Decision point 2 — What you find.** The sender is `helpdesk@yourcompany-support.net` (your company uses `yourcompany.com`), and the link destination does not match your company's domain.
A) Proceed anyway — IT may use a vendor.
B) Close it, open your company's real IT page or password portal by typing its address yourself, and check your password status there.
C) Click but do not enter your current password, only a new one.
D) Call the phone number in the email to ask.

**Correct path: B.** A vendor explanation is possible, which is why you verify through the real portal instead of guessing. Entering any password (**C**) hands it over, and the email's phone number (**D**) is part of the suspect message.

**Decision point 3 — A coworker says they already clicked and signed in.**
A) Tell them not to worry if nothing looks wrong yet.
B) Tell them to change their password immediately on the real portal, turn on MFA, and report it to IT right away.
C) Advise them to delete the email so there is no record.
D) Suggest waiting until noon to see if accounts lock.

**Correct path: B.** Speed and reporting are the whole defense. A changed password plus MFA can make the credential useless, and IT can check for other recipients and mailbox rules. Deleting evidence (**C**) helps only the attacker.

**Decision point 4 — Later that day, a text arrives:** "IT: Your reset was incomplete. Complete here: [link]."
A) Use it — it follows up on this morning's issue, so it must be connected and real.
B) Treat it as a new, unverified message: ignore the link, and check only through the real portal or a known IT number.
C) Reply STOP.
D) Enter your credentials quickly before it expires.

**Correct path: B.** Attackers run email and text waves together so the second message borrows credibility from the first. Each message earns trust on its own evidence — or it does not. **C** confirms your number is active.

## Knowledge check

1. You get a text: "Your package couldn't be delivered, update your address here: [link]." You are not expecting a package. Safest move?
   A. Click — maybe it is a surprise gift
   B. Reply STOP to opt out
   C. Ignore the link, and check tracking in the carrier's real app or site, typed by you
   D. Forward it to friends, then click to check

2. An email link reads "bankofamerica.com," but hovering shows the destination is `bankofarnerica-login.com`. What does that tell you?
   A. Nothing — the visible link text is what matters
   B. It is legitimate; banks use alternate domains
   C. It is phishing — the real destination does not match the claimed one
   D. Your browser is misreading the address

3. You just typed your email password into a fake login page. What is the FIRST thing to do?
   A. Email the sender and demand they delete it
   B. Change your email password immediately on the real site and enable MFA
   C. Wait and see if anything bad happens
   D. Delete the phishing email so you do not click it again

4. A parking meter has a QR code for payment that looks like a sticker placed over the original. What should you do?
   A. Scan it — printed codes are official
   B. Scan it, but pay quickly so the session does not expire
   C. Avoid that code; pay another way or use the parking service's real app, and check any address your phone shows before entering payment details
   D. Peel it off and scan whatever is underneath

### Answer key

1. **C.** Unsolicited delivery texts with links are a standard lure, and any real problem is visible in the carrier's own app. **B** confirms your number is live, and **A** and **D** walk into the harvest page the message exists to deliver you to.
2. **C.** Attackers control the visible text; only the real destination tells the truth, and lookalike spellings are a classic tell. **A** and **B** are exactly the assumptions the fake relies on.
3. **B.** Speed matters — a password changed on the real site, with MFA on, can become useless to the attacker within minutes. **C** gives them the head start they need, while **A** and **D** change nothing about their access.
4. **C.** A sticker is a classic way to replace a legitimate code with a payment-harvesting one; the physical setting proves nothing. **D** could expose yet another unknown code and is not needed when the app or another payment method works.

## Key takeaways

- Phishing succeeds with pressure, not perfection — urgency, threats, and deadlines are the tell, not the excuse to hurry.
- Verify through a channel you choose: open the real app or type the real address yourself, every time.
- Attackers control the display name and link text. The full sender address and real link destination are where the truth is.
- Texts and QR codes are phishing too. Forward spam texts to 7726, and read a QR code's destination before you enter anything.
- Never pay a "problem" with gift cards, a wire, or crypto.
- If you clicked, act in order and fast: change passwords on the real site, call the bank on the number on your card, scan devices, and report.
- Report and warn others — a reported message protects the next person.

## Glossary

**Phishing** — A fake message impersonating a trusted sender to trick you into clicking, opening an attachment, or giving up credentials or money.

**Smishing** — Phishing delivered by text message (SMS). The tactics and defenses are the same as email phishing.

**Credential harvesting** — Collecting usernames and passwords, usually with a fake sign-in page that records what you type.

**Lookalike domain** — A web address made to resemble a real one with small changes — swapped letters or added words — such as `bankofarnerica-login.com`.

**Malicious attachment** — A file sent with a message that opens a fake sign-in page or installs harmful software when opened.

**Business email compromise** — An attack using a compromised or impersonated work mailbox to redirect payments or steal credentials, often from inside a real email thread.

**QR code phishing** — Using a QR code to send you to a fake sign-in or payment page. Scanning is the same as clicking an unknown link.

**7726** — The number US mobile carriers use for reporting spam texts. It spells SPAM on a phone keypad.

## Further reading

- Federal Trade Commission — https://consumer.ftc.gov
- Report fraud — https://reportfraud.ftc.gov
- FBI IC3 — https://www.ic3.gov
- CISA — https://www.cisa.gov

## Certification alignment

**Supports:** CompTIA Security+ (SY0-701) Domain 2 — social engineering and phishing recognition.

Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
