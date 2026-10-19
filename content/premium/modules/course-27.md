Operating Systems & Troubleshooting
MODULE OVERVIEW
Level: Beginner | Time: 75-90 minutes | Prerequisites: Hardware Essentials or equivalent.

LEARNING OBJECTIVES
After this module you can:
- Choose a clean install, upgrade, or repair install for the right situation
- Use core admin tools in Windows, macOS, and Linux to inspect a system
- Set account and OS security settings that block common attacks
- Troubleshoot a software fault methodically, not by reinstalling on instinct
- Work to professional standards: safety, documentation, and change awareness

LESSON 1 — INSTALLS, ADMIN TOOLS, AND ACCOUNT SECURITY
A clean install wipes the drive and starts fresh: right for a new drive, a corrupted system, or repurposing a machine. An upgrade keeps files and apps: right when the system is healthy. A repair install fixes OS files while keeping data. Always: back up first, verify the backup opens, and check hardware requirements.
Admin tools: Windows — Task Manager, Event Viewer, ipconfig, sfc /scannow. macOS — Activity Monitor, Disk Utility, Terminal. Linux — top, df -h, journalctl.
Baseline security: daily work on a standard account, admin only for changes; sign-in on wake; automatic updates and firewall on; encrypt the drive (BitLocker, FileVault, LUKS); lock the screen when idle.
CASE BREAKDOWN: Illustrative walkthrough — a bookkeeper runs everything as administrator "because it is easier." A fake invoice attachment runs with full rights and installs remote-access software a standard account could not have allowed. It could have stopped at account design: a standard account would have demanded an admin password the malware did not have. The signal most people miss: an admin prompt you did not trigger is a stop sign, not a nuisance.
New-machine checklist:
1. Install the OS and all updates; restart.
2. Create a standard daily account; give the admin account a strong, unique password.
3. Turn on encryption, firewall, and automatic updates.
4. Remove unwanted bundled software.
5. Back up; verify a test file restores.
COMMON MISTAKE: Doing daily work as administrator — it removes the last prompt before full control.

LESSON 2 — SOFTWARE TROUBLESHOOTING AND WORKING PROFESSIONALLY
Use the six-step method: identify, theorize, test, plan, implement, verify and document. Clues: Did it ever work? What changed? Does it fail for one user, one file, or everyone? Does Safe Mode or a test account fix it? Likely causes, in order: a recent update, low disk space, a corrupt profile, a stopped service, wrong permissions, then malware. Test simple first: restart, check disk space, try another account, read logs at the failure time, undo the last change.
Operational procedures are part of the repair. Safety: unplug before opening a case and dispose of batteries as e-waste, not trash. Documentation: log symptom, cause, fix, and time. Change awareness: on a system others depend on, state what will change, what could break, and the rollback — before starting. Professionalism: explain plainly, do not browse private files, keep credentials out of tickets.
CASE BREAKDOWN: Illustrative walkthrough — after an overnight update, a design app crashes for one user only. Testing shows it opens under a test account, so the install is sound; that user's profile holds a corrupt settings file. Renaming it lets the app rebuild it. It could have stopped at identify: "one user" ruled out the shared install. The signal most people miss: scope — one user, one machine, or everyone — is the fastest fault divider you have.
Software fault checklist:
1. Record the error, time, and who is affected.
2. Ask what changed; check updates and installs.
3. Test another file, account, Safe Mode.
4. Check disk space, services, and logs.
5. Apply one fix, verify, document.
COMMON MISTAKE: Reinstalling first. It destroys evidence and often imports the same corrupt profile back.

HANDS-ON EXERCISE
On a PC you own or on paper: a browser crashes on one website and the PC reports low disk space.
Decision point 1: Disk is 99 percent full. Clear space or reinstall the browser? Correct path: Clear space first — a full disk corrupts profiles and blocks updates.
Decision point 2: Space freed; the browser still crashes on that one site only. Correct path: Test a private window with extensions off and a second browser. One-site failure points to the site, cache, or an extension.
Decision point 3: A family member wants updates turned off. Correct path: Explain that updates patch holes attackers use; agree a convenient restart time instead.

KNOWLEDGE CHECK
[CHECK]
Q: Daily work should run under which account type, and why?
A: Administrator, so prompts never interrupt work
B: Standard, so malware and mistakes lack full rights by default
C: Guest, so nothing can ever be installed
ANSWER: B
FEEDBACK: A standard account forces an admin prompt before deep changes, stopping much malware. Admin gives a bad click full control.
[/CHECK]
[CHECK]
Q: An app fails for one user but works under a test account. Most likely cause?
A: The shared app install is corrupt
B: The network is down
C: That user's profile or settings are corrupt
ANSWER: C
FEEDBACK: Scope divides the fault: one user affected points to that profile. Reinstalling for everyone wastes time and misses the cause.
[/CHECK]
[CHECK]
Q: Before a clean install, the non-negotiable first step is:
A: Back up the data and verify the backup opens
B: Delete the old user accounts
C: Turn off the firewall
ANSWER: A
FEEDBACK: A clean install wipes the drive. An unverified backup may be empty or corrupt, so prove it opens before erasing anything.
[/CHECK]

KEY TAKEAWAYS
- Clean install, upgrade, and repair install solve different problems; back up and verify first
- Daily work on a standard account; admin is for changes only
- Encryption, firewall, updates, and screen lock are baseline settings
- Scope — one user, one machine, everyone — is the fastest fault divider
- Safety, documentation, and agreed changes are part of the job

GLOSSARY
Clean install — Installing an OS onto a wiped drive, starting fresh
Standard account — Daily account without rights to make deep system changes
Drive encryption — Scrambling disk contents so a stolen device exposes nothing
Event Viewer — Windows log tool recording system and application events
User profile — Per-account settings that can corrupt independently
E-waste — Electronic waste needing proper disposal, such as batteries

FURTHER READING
CompTIA A+ exam objectives: https://www.comptia.org
Microsoft Windows documentation: https://learn.microsoft.com

CERTIFICATION ALIGNMENT
Supports: CompTIA A+ Core 2 (220-1102) — operating systems, security, software troubleshooting, and operational procedures domains.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately through the certification body.
