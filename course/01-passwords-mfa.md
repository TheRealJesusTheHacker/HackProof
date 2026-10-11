# Passwords & MFA — Lock Your Digital Doors

## What it is

A password is the key to an account. A **password manager** is a locked vault
that remembers all your keys for you — you memorize one strong master
password, and it generates and fills in a unique, random password for every
site. **MFA (multi-factor authentication)** means proving it's you in two
ways instead of one: something you know (your password) plus something you
have (your phone, an app, or a physical security key). You'll also see it
called "two-step verification" or "2FA" — same idea.

A **passphrase** is a password made of several random words strung together,
like `correct-horse-battery-staple` (don't actually use that one — it's
famous now). Passphrases are long, which makes them strong, but still
possible for a human to remember. They're for the handful of passwords you
actually have to type yourself, like your password manager's master password
or your computer login.

## Why it matters

Most "hacking" isn't some genius guessing your password letter by letter.
It's way lazier than that: attackers get giant lists of real usernames and
passwords from data breaches, then let software try those same combinations
on banks, email, shopping, and social media sites automatically. This is
called **credential stuffing** — stuffing stolen logins into other sites to
see which ones open. If you reuse passwords, one breach anywhere becomes a
breach everywhere. A unique password per site plus MFA shuts this whole
attack down cold.

## How the attack really works

**Example 1 — The reused password.** In 2019 you signed up for a free recipe
forum with the same password you use for your email. The forum gets breached
and its login list leaks online. Months later, an attacker feeds your
email + that password into an automated tool that tries it on Gmail, your
bank, Amazon, Facebook, and dozens of other sites. Your email opens. Now
they click "forgot password" on your bank, the reset link goes to the email
they now control, and they're in. They never "hacked" your bank — they
walked in through your reused password.

**Example 2 — The phishing harvest.** You get a text that looks like it's
from your bank: "Suspicious activity detected, verify now." The link goes
to a fake login page that looks exactly like your bank's site. You type your
username and password. The fake page shows an error; the real bank page
would never load. Behind the scenes, the attacker now has your credentials
and tries them on your email and other accounts within minutes — betting
you reuse them.

**Example 3 — The SMS code intercept.** You actually have MFA turned on, but
it's the text-message kind. An attacker calls your phone company pretending
to be you ("I lost my phone, please move my number to this new SIM"). If
the rep believes them, your number moves to the attacker's phone and your
MFA codes start arriving on *their* device. This is called **SIM swapping**,
and it's exactly why texted codes are the weakest form of MFA — better than
nothing, but an authenticator app or security key can't be stolen with a
phone call.

## Action checklist (do these today)

- [ ] **Install a password manager.** Bitwarden is free, open-source, and
      works on phones and computers. Your browser's built-in password saver
      is better than nothing, but a dedicated manager works everywhere and
      warns you about reused or breached passwords.
- [ ] **Turn on MFA on the password manager itself.** It's the vault — lock
      the vault twice.
- [ ] **Change your most important passwords first, in this order:** your
      email accounts (email is the master key — password resets go there),
      then banking and money apps, then everything else. Let the manager
      generate a long random password for each one.
- [ ] **Kill password reuse.** Every site gets its own password. You don't
      have to do all 200 accounts tonight — start with email, money, and
      anything tied to your identity, then work through the rest over a
      couple weeks.
- [ ] **Turn on MFA everywhere that offers it** — especially email, banking,
      social media, and cloud storage. Use an authenticator app (like
      Google Authenticator, Microsoft Authenticator, 2FAS, or Authy) instead
      of texted codes whenever you get the choice. If a site offers a
      physical security key (like a YubiKey) and you want maximum protection,
      that's the strongest option there is.
- [ ] **Pick your passphrases.** For the few passwords you must memorize
      (manager master password, computer login), use 4–6 random words. Your
      password manager can generate one.
- [ ] **Save your MFA backup/recovery codes** somewhere safe (printed and
      stored, or in the password manager's secure notes). If you lose your
      phone without these, getting back into your accounts is painful.

## Red flags

- An email from a company saying "we experienced a data breach" — act on
  it, don't file it away.
- Your browser or password manager warns "this password appeared in a data
  breach" — change that password (and anywhere else you used it).
- Login alert emails or texts for accounts you didn't just sign into.
- A site suddenly asking you to re-verify by text when you normally use an
  app — could be an attacker mid-takeover.

## What to do after a breach

1. **Check [haveibeenpwned.com](https://haveibeenpwned.com)** — type in
   your email address. This free, legitimate service (run by security
   researcher Troy Hunt) tells you which known breaches exposed your
   address and what was taken.
2. **Change passwords in this order:** the breached account first, then your
   email account, then *every other account* that shared the breached
   password. Same password anywhere else = change it there too.
3. **Turn on MFA** on all of those accounts if it isn't on already.
4. **If your email was breached**, check its settings for forwarding rules
   or filters you didn't create — attackers sometimes add a rule that
   silently forwards your incoming mail (including password resets) to
   them even after you change the password. Delete anything you didn't set
   up.
5. **Watch your money and credit** for anything odd in the following weeks.
   If card numbers were exposed, call your bank about a replacement.

## Quiz

**Q1.** You used the same password for a gaming forum and your email, and
the forum gets breached. What's the first account you should secure?
A) The gaming forum
B) Your email
C) Your social media
D) None — the forum password doesn't matter now

**Q2.** Which form of MFA is hardest for an attacker to defeat with a phone
call to your carrier?
A) Codes texted to your number (SMS)
B) An authenticator app on your phone
C) Answering a "security question" like your mother's maiden name
D) Getting the code emailed to you

**Q3.** Your password manager can remember everything for you. Which
password is the MOST important one to make strong and memorable?
A) Your streaming service password
B) Your password manager's master password
C) Your food delivery app password
D) They're all equally important

---

### Answer key

**Q1 — B.** Your email is the master key: password resets for your bank and
everything else flow through it. Secure the breached account too, but email
comes first.

**Q2 — B.** An authenticator app generates codes on your device — a SIM swap
can't steal them. Texted codes (A) go to whoever controls your number.
Security questions (C) are guessable and often public; emailed codes (D)
fail if your email is compromised.

**Q3 — B.** The master password protects the vault holding all your other
passwords. Make it a long passphrase and never reuse it anywhere.
