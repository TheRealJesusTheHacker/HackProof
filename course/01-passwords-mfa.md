# Passwords & MFA — Lock Your Digital Doors

## Module overview

**Level:** Foundations
**Estimated time:** 45–55 minutes
**Prerequisites:** None. If you have an email account and a phone, you can start.

### Learning objectives

After this module you can:

- Explain how credential stuffing turns one breached password into access to many accounts.
- Set up a password manager, create a strong master passphrase, and let the manager generate unique passwords for you.
- Choose the strongest MFA method a site offers and explain why an app or security key beats texted codes.
- Secure accounts in the right order — email first — and store recovery codes safely.
- Respond to a breach by changing the right passwords, turning on MFA, and checking email for hidden forwarding rules.

## Lesson 1 — Why password reuse breaks everything

A password is the key to an account. Use the same key for your house, car, and safe, and losing one copy puts all three at risk. Online it happens faster — and you may never know the copy was lost.

Most takeovers do not start with guessing. Attackers collect huge lists of usernames and passwords exposed in breaches, then software tries those combinations automatically on email, banking, shopping, and social media. That is **credential stuffing** — stuffing stolen logins into other sites to see which ones open.

It works only because people reuse passwords. You sign up for a small forum with the same password you use for email. That site gets breached, and now your email password is on a list being tested everywhere. One breach becomes a breach everywhere.

Email is the master key. Password resets for your bank and other accounts land in your email, so anyone who controls your email can reset passwords downstream and lock you out.

### Case breakdown

**The reused password — step by step**

1. In 2019, Maya joins a free recipe forum using her email address and the same password she uses for that email.
2. The forum is breached. Its user list leaks and is combined with other breach lists.
3. Months later, an automated tool tries Maya's email and that password at major email providers. It opens.
4. The attacker searches the inbox for "bank" and "reset," requests a bank password reset, and uses the link that arrives in the inbox they control.
5. They change the bank password and add a forwarding rule copying new mail to an outside address, deleting alerts so Maya sees nothing unusual.

**Where it could have been stopped:** Step 3. A unique forum password would have opened the forum and nothing else. MFA on email would also have stopped it — the password alone would not have been enough.

**The signal most people miss:** The breach notice from a "small, unimportant" site. Attackers are not after the forum. They are after everywhere else you used that password.

**Defensive procedure**

- Treat every breach notice as an emergency for *every* account that shared that password.
- Prioritize: email, password manager, banking and money apps, then everything else.

> **Common mistake:** Changing only the breached account and leaving the same password live on your email and bank. The breached site was the source of the key, not the main target.

## Lesson 2 — Password managers and passphrases that work

You cannot remember a different long, random password for every account. You are not supposed to. A **password manager** is a locked vault that remembers them for you: you memorize one master password, and it generates, stores, and fills unique random passwords for you.

Bitwarden is a solid start: free, open-source, and available everywhere. A dedicated manager beats a browser saver because it works in more places and warns about reused or breached passwords.

For the few passwords you still type — your master password and computer login — use a **passphrase**: several random words together, like `correct-horse-battery-staple`. Do not use that one; it is famous now. Aim for four to six random words with no personal connection. No pet names or birthdays — attackers try those first.

### Case breakdown

**Three passwords for forty accounts — step by step**

1. James keeps passwords in a notebook. To keep the list short, he uses three passwords across almost forty accounts.
2. A shopping site he uses is breached. One of those three passwords is exposed.
3. Within days, strangers use his streaming account, and his email shows reset requests he did not make.
4. James must change that password in dozens of places, from memory, under pressure. He misses two accounts — one is an old shopping account with a saved card.

**Where it could have been stopped:** At setup. A manager would have given each account its own password, so the shopping breach stayed a shopping problem.

**The signal most people miss:** The reuse warning — "used on 6 sites" or "appeared in a data breach" maps how far one leak will spread.

**Setup checklist**

- [ ] Install the manager on phone and computer and create your account.
- [ ] Create a master passphrase of four to six random words. Write it on paper, store it safely at home while you memorize it, and never reuse it.
- [ ] Turn on MFA on the manager itself. Lock the vault twice.
- [ ] Add accounts in order: email first, then banking and money, then shopping and social media. Let the manager generate each new password.
- [ ] Work through the rest over a couple of weeks — you do not have to fix 200 accounts tonight.
- [ ] Save backup and recovery codes in the manager's secure notes, or printed and stored safely.

> **Common mistake:** Using a variation when forced to change, like `Summer2024!` then `Summer2025!`. Variations are predictable. Let the manager generate something random — you never have to type it.

## Lesson 3 — MFA done right: apps, keys, and SIM swapping

**MFA (multi-factor authentication)** means proving it is you in two ways: something you know (your password) plus something you have (your phone, an app, or a physical security key). You will also see it called 2FA or two-step verification.

MFA matters because passwords leak. With MFA on, a stolen password alone is not enough. Not all MFA is equal:

- **Texted codes (SMS)** — better than nothing, but weakest. The code goes to whoever controls your number, and numbers can be moved.
- **Authenticator apps** — generate codes on your device, changing every 30 seconds. The code never travels over the phone network, so moving your number does not move your codes.
- **Push approvals** — generally stronger than SMS when they show what you are approving and where the sign-in is from.
- **Physical security keys** (like a YubiKey) — strongest for most people. You tap or insert the key to prove you are present. There is no code to intercept or read aloud.

### Case breakdown

**The SMS code intercept — step by step**

1. You use text-message MFA, and an attacker already has your password from a phishing page.
2. The attacker calls your carrier pretending to be you: "I lost my phone, please move my number to this new SIM."
3. The rep is convinced. Your number moves to the attacker's SIM — this is **SIM swapping**. Your texts now go to their device.
4. The attacker signs in with your password and requests the code. It arrives on *their* phone. They enter it and they are in.
5. You notice your phone has lost service. By the time you reach the carrier, resets are already underway.

**Where it could have been stopped:** At MFA setup. An app generates the code on your original device — swapping your SIM does not move it. A carrier PIN or port-out lock also makes your number harder to move on a story alone.

**The signal most people miss:** Sudden loss of cell service. If your phone drops to "no service" and stays there, treat it as a security event — contact your carrier from another phone and check email and bank accounts.

**MFA checklist**

- [ ] Turn on MFA for email first, then banking, social media, cloud storage, and your manager.
- [ ] Pick authenticator app over text where you have a choice. Pick a security key for high-value accounts where offered.
- [ ] Set a carrier PIN or port-out / number lock so your number cannot be moved on a call alone.
- [ ] Never approve a push prompt you did not trigger, and never read an MFA code aloud. No real support team needs either.

**What to say if someone asks for your code:** "I don't share verification codes. I'm going to hang up and call the number on the back of my card, and I'll sort it out there." Then do that.

> **Common mistake:** Approving every prompt out of habit. Attackers with your password will trigger prompts repeatedly hoping you tap Approve to make them stop. It only works if you approve a sign-in you did not start.

## Lesson 4 — Recovery codes and cleaning up after a breach

Recovery settings decide what happens when you lose your phone or a site is breached.

Save backup codes when you turn on MFA. Without them, a lost phone can lock you out for days. Store codes printed somewhere safe at home, or in your manager's secure notes — not only on that phone. Review recovery emails and numbers yearly; an old address you no longer control is an open side entrance.

### Case breakdown

**The forwarding rule left behind — step by step**

1. An attacker gets into Dana's email through a reused password and spends a quiet hour inside.
2. Before leaving, they add a filter: mail containing "reset," "verify," or her bank's name is forwarded outside and marked as read.
3. Dana changes her email password and turns on MFA. She believes she is done.
4. Two weeks later, a bank reset she did not request succeeds — the reset email was forwarded to the attacker and hidden from her.

**Where it could have been stopped:** At cleanup. Changing the password closed the front door, but nobody checked the rules left behind. A two-minute review of forwarding, filters, and signed-in devices would have caught it.

**The signal most people miss:** Missing mail. If statements or reset emails stop arriving or appear already read, check filters and forwarding before assuming a glitch.

**After a breach — in order**

1. Check haveibeenpwned.com for your email. This free, legitimate service, run by security researcher Troy Hunt, shows which known breaches exposed your address and what was taken.
2. Change the breached account first, then your email, then every account that shared that password. Let your manager generate each new one.
3. Turn on MFA — app-based where possible — on all of those accounts.
4. If email was involved, check forwarding addresses, filters, recovery settings, and signed-in devices. Delete anything you did not create and sign out sessions you do not recognize.
5. Watch money and credit in the following weeks. If card numbers were exposed, call the number on the back of your card about a replacement. If identity details were exposed, consider a free credit freeze at Equifax, Experian, and TransUnion — free, and liftable when you apply for credit.

> **Common mistake:** Treating a lost phone as only a phone problem. It holds your authenticator, email, and manager access. Lock it remotely if you can, and secure email and banking from another device first.

## Hands-on exercise

**Scenario:** A photo-printing site you used two years ago says its database was breached and passwords were exposed. You likely used your usual password there — the same one you still use for email and a shopping site.

**Decision point 1 — Where do you start?**
A) Delete the email; the site is too small to matter.
B) Change the photo site's password only.
C) Change your email password first with a manager-generated password, turn on app-based MFA, then change the photo site and shopping site.
D) Warn friends first.

**Correct path: C.** Email is the master key and shares the password, so securing it first protects every reset that flows through it. **A** leaves the stolen password working; **B** is the most common incomplete fix.

**Decision point 2 — Picking email protection.** MFA is offered by text, authenticator app, or security key. You already use an authenticator app for work.
A) Text message — it is familiar.
B) Authenticator app.
C) Skip MFA; the new password is long.
D) Codes emailed to the same inbox.

**Correct path: B.** App codes live on your device and survive a SIM swap. **D** is circular — codes sent to the account you are protecting prove nothing if it is compromised. A long password (**C**) helps, but MFA makes a future leak survivable.

**Decision point 3 — Master password.** You choose:
A) Your dog's name and birth year, so you will not forget.
B) The same strong password you used for email before.
C) A passphrase of five random words used nowhere else, written on paper and stored safely until memorized.
D) A short PIN for speed.

**Correct path: C.** The master password guards the vault holding everything else, so it must be long, unique, and unrelated to findable facts. **B** imports that password's breach history into your vault.

**Decision point 4 — One week later.** A bank statement email never arrives and a reset email shows as already read.
A) Assume the bank's email is glitchy.
B) Check forwarding addresses, filters, recovery settings, and signed-in devices right away.
C) Change your bank password again and move on.
D) Turn off login alerts.

**Correct path: B.** Missing or pre-read mail after a compromise points to a forwarding rule left by the attacker. Changing passwords again (**C**) does not remove that rule — the rule is how the attacker keeps receiving reset links.

## Knowledge check

1. Your email and a gaming forum share a password, and the forum is breached. Which account do you secure first?
   A. The gaming forum, because it was breached
   B. Your email, because password resets for other accounts flow through it
   C. Your social media, because it is most visible
   D. None — a forum password does not matter

2. Which MFA method is hardest to defeat by calling your carrier and moving your number?
   A. Codes texted to your number
   B. An authenticator app on your device
   C. Security questions about your childhood
   D. Codes emailed to you

3. What makes a good master password for a password manager?
   A. A short password you type quickly
   B. Your strongest old password, reused because it worked well
   C. A long passphrase of four to six random words used nowhere else
   D. A family name plus a memorable date

4. After an email compromise, you changed your password and turned on MFA, but reset emails keep vanishing. What next?
   A. Your spam folder only
   B. Forwarding addresses, filters and rules, recovery settings, and signed-in devices
   C. Whether your contacts got the same breach email
   D. Nothing — MFA guarantees the problem is over

### Answer key

1. **B.** Email is the master key: whoever controls it can reset your bank and other accounts. **A** matters too, but second. **C** and **D** leave the reset pathway open — exactly what attackers use after a breach.
2. **B.** App codes are generated on your device, so a SIM swap cannot steal them. **A** goes to whoever controls the number, **C** relies on findable facts, and **D** fails if your email is compromised.
3. **C.** Length plus uniqueness protects the vault, and random words stay memorable for you. **B** imports an old password's exposure, while **A** and **D** trade strength for convenience or guessable facts.
4. **B.** Attackers commonly leave forwarding rules that copy reset mail to them after a password change. **A** misses the mechanism, and **D** is false comfort — MFA protects sign-in, not rules already saved inside the account.

## Key takeaways

- Password reuse is the vulnerability — one breach becomes every breach when the same password opens your email.
- Email is the master key. Secure it first, with a unique password and MFA, before anything else.
- A password manager does the remembering so every account can have its own long, random password.
- For passwords you must memorize, use a passphrase of four to six random words — never personal facts or variations.
- App-based MFA beats texted codes because a SIM swap can steal your number but not your app. Security keys are strongest where offered.
- Save recovery codes somewhere safe that is not only on your phone.
- After any compromise, check forwarding rules, filters, and signed-in devices — a password change alone does not evict an attacker.

## Glossary

**Password manager** — A tool that stores passwords in an encrypted vault, generates a unique random password per site, and fills them in for you.

**Passphrase** — A password built from several random words. Its length makes it strong while staying memorable.

**MFA (multi-factor authentication)** — Requiring two kinds of proof at sign-in, such as a password plus a code from your device. Also called 2FA or two-step verification.

**Credential stuffing** — Automatically trying username and password pairs stolen in one breach against many other sites, hoping for reuse.

**SIM swapping** — Convincing a carrier to move your number to a SIM the attacker controls, so your calls and texted codes go to them.

**Authenticator app** — An app on your device that generates short, time-based sign-in codes locally, without using the phone network.

**Security key** — A small physical device you tap or plug in to confirm a sign-in, with no code to intercept or read aloud.

**Recovery codes** — One-time backup codes issued when you enable MFA, letting you back in if you lose your usual sign-in device.

**Forwarding rule / filter** — An email setting that copies, moves, or hides mail. Attackers add hidden rules to keep receiving your reset emails.

## Further reading

- Federal Trade Commission — https://consumer.ftc.gov
- IdentityTheft.gov — https://www.identitytheft.gov
- CISA — https://www.cisa.gov
- FBI IC3 — https://www.ic3.gov
- AnnualCreditReport.com — https://www.annualcreditreport.com

## Certification alignment

**Supports:** CompTIA Security+ (SY0-701) Domains 1 and 3 — identity and access management concepts and implementation (MFA, password policy); CompTIA A+ Core 2 (220-1102) operating-system security settings.

Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
