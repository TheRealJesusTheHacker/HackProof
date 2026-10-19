MODULE OVERVIEW
Level: Intermediate | Time: ~20 minutes
Prerequisites: none

LEARNING OBJECTIVES
After this module you can:
- Explain how attackers take over an account without knowing your password
- Recognize session theft and malicious inbox rules
- Recover a compromised account in the correct order, starting with email
- Lock down recovery options so a takeover cannot repeat itself

LESSON 1 — HOW ACCOUNTS ARE TAKEN OVER
A takeover does not always start with a guessed password. Attackers steal session cookies, the small files your browser uses to prove you are already signed in. Malware or a fake sign-in page can capture that session and replay it, sometimes bypassing a password prompt entirely. Once inside, the attacker changes the password and swaps the recovery phone and email.

Email is the master key. Whoever controls your inbox can reset passwords for your bank, shopping, and social accounts. That is why attackers who reach your email often stay quiet first, creating inbox rules that forward bank messages or hide security alerts in a folder you never open.

CASE BREAKDOWN: A user installs a free tool from an ad. Days later, friends report odd messages from her social account. She resets that password and moves on. What happened: the malware took her email session too, and hidden inbox rules let the attacker intercept reset emails and take two more accounts. Where it could have stopped: at the email account, where checking rules and sessions would have revealed the real breach. The signal most people miss: being signed out of several accounts in one week is one incident, not bad luck.

Check monthly: review active sessions, inbox rules, and forwarding on your email and main accounts, and remove anything you do not recognize.

COMMON MISTAKE: Changing only the password of the account that looks compromised. If the email behind it is controlled by someone else, every new password can be reset again.

LESSON 2 — RECOVERY IN THE RIGHT ORDER
Order matters because each step protects the next one. Work from a clean device you trust that was not involved in the compromise. If your computer may carry malware, borrow a trusted device for the first steps, and do not sign in to sensitive accounts from the suspect device until it is cleaned.

Recovery order:
- First, secure your email: change its password, sign out all other sessions, turn on app-based or key-based multi-factor authentication, and delete unknown inbox rules and forwarding.
- Second, secure your bank and payment accounts, then any account that can spend money.
- Third, secure social and messaging accounts, which attackers use to scam your contacts.
- Fourth, review recovery addresses and phone numbers everywhere, and replace any you did not set. Then tell your contacts what happened.

Use a password manager so every account has a different password. Reuse lets one breach unlock the next account.

CASE BREAKDOWN: A man finds his shopping account ordering gift cards. He cancels the orders, changes that password, and relaxes. A week later his bank password is reset through his email, which he never checked. He repaired the symptom and left the master key exposed. Email first would have closed the reset path. The signal most people miss: the first account you notice is rarely the first one the attacker took.

COMMON MISTAKE: Turning multi-factor authentication back on with the same phone number and recovery options the attacker may have changed. Verify every recovery detail yourself before you rely on it.

HANDS-ON EXERCISE
Situation: You cannot sign in to your email. The password you are sure is correct is rejected, and your bank has just sent a password-reset notice to that same inbox.

Decision point 1: A friend offers to try your old password repeatedly from your laptop. Correct path: stop. Repeated attempts can lock the account, and the laptop may be part of the problem.
Decision point 2: You regain email through the provider's recovery process. Correct path: before anything else, change the password, sign out all sessions, check inbox rules and forwarding, and turn on strong multi-factor authentication.
Decision point 3: Email is secure. Correct path: work outward in order: bank and payment accounts next, then social accounts. Each gets a new, unique password.

KNOWLEDGE CHECK
[CHECK]
Q: Why do you secure email before other accounts during recovery?
A: Email inboxes are the largest accounts you own
B: Whoever controls your email can reset passwords for your other accounts
C: Email providers respond faster than banks
ANSWER: B
FEEDBACK: Email is the master key for password resets, so it must be secured first or later fixes can be undone.
[/CHECK]
[CHECK]
Q: What does a malicious inbox rule typically do?
A: It deletes your contacts so you cannot warn them
B: It forwards or hides messages, such as bank alerts and reset notices
C: It changes your email password every day
ANSWER: B
FEEDBACK: Hidden rules let an attacker intercept alerts and resets while your inbox looks normal.
[/CHECK]
[CHECK]
Q: What is session theft?
A: Stealing the cookie that proves you are signed in, so no password is needed
B: Watching someone type in a public place
C: Guessing a password from a birthday
ANSWER: A
FEEDBACK: A stolen session can be replayed to enter an account as if the attacker were you.
[/CHECK]

KEY TAKEAWAYS
- Email is the master key. Protect it first and recover it first.
- Check active sessions, inbox rules, and forwarding for anything you did not set.
- Recover from a clean device, in order: email, money accounts, then social accounts.
- Give every account a unique password stored in a password manager.
- Being signed out of several accounts at once is one incident, not a coincidence.

GLOSSARY
Account takeover — An attacker gaining control of an account that belongs to someone else.
Session cookie — A file a site uses to remember that a browser is already signed in.
Session theft — Stealing that cookie to impersonate the signed-in user.
Inbox rule — An automatic instruction that moves, forwards, or hides incoming email.
Password manager — A tool that creates and stores a unique password for each account.

FURTHER READING
- FTC guidance on hacked accounts and identity theft: https://consumer.ftc.gov
- Identity theft recovery steps: https://www.identitytheft.gov
- FBI Internet Crime Complaint Center: https://www.ic3.gov

CERTIFICATION ALIGNMENT
Supports: CompTIA Security+ (SY0-701) Domains 3 and 4 — account-compromise indicators and response.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
