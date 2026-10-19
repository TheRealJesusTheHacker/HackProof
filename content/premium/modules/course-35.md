Exploitation & Post-Exploitation Basics

MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Ethical Hacking Methodology; networking fundamentals.

LEARNING OBJECTIVES
After this module you can:
- Explain password attack classes and their defenses
- Name the main web application attack classes and their causes
- Describe privilege escalation and post-exploitation
- State what defenders detect during each activity
- Document exploitation work for reporting

LESSON 1 — HOW PROFESSIONALS THINK ABOUT EXPLOITATION
Authorization rule: test only with written permission from the system owner, for the systems and time window named in it. No written permission and no defined scope means no testing. Practice only on systems you own or in official labs.

Professionals start from a finding, not a tool. Confirm the target is in scope, identify a known weakness class that fits the evidence, and test at the minimum level that proves it.

Password attacks: at concept level, these guess or reuse credentials — common passwords, credentials from a breach, or defaults never changed. Defenders watch for many failed logins and success after repeated failures. Recommend unique passwords, multi-factor authentication, lockout, and alerting.
Web application attacks: OWASP classes include injection, broken access control, and misconfiguration. The common cause is an application trusting input or failing to check who may do what. Defenders watch logs for malformed input and access outside a user's role.
Work one class at a time and stop at proof.

CASE BREAKDOWN: In an authorized lab assessment, a tester logs in to a training application once with a documented default administrator credential, screenshots the settings page without changing anything, logs out, and reports a critical finding. Proof took one login; creating accounts or altering data was risk without value.

Procedure — testing a weakness class:
1. Confirm target and method are in scope.
2. Note what you expect to prove before you act.
3. Act once, at the minimum level that proves it.
4. Save output, screenshots, and timestamps.
5. Record the defensive signal a client should have seen.

COMMON MISTAKE: Running an exploitation tool across a whole network because it is available. Scope, not the tool menu, decides what you test.

LESSON 2 — PRIVILEGE ESCALATION AND POST-EXPLOITATION
Privilege escalation means moving, in concept, from a low-privilege account to higher privileges through a weakness such as excessive permissions, unpatched local services, or credentials readable by low-privilege users. Test whether the path exists and document the condition that allows it. Defenders watch for new privileged accounts and access to credential stores.

Post-exploitation follows proved access: confirm what that account can reach, check whether sensitive data is exposed to it, and record it. Note that data was reachable; do not copy client data beyond what the rules expressly allow, and keep none after the engagement except as the agreement requires.

Each report entry needs: system, weakness class, evidence, business impact, what defenders should have detected, and a fix.

CASE BREAKDOWN: A tester with a standard lab account can read a folder of service account details because permissions were set for all staff. He records the path and permissions, opens nothing beyond one listing as evidence, and reports it. The finding is the permission design, not the contents; the fix is least-privilege access.

Checklist — closing a finding:
- Evidence saved with timestamps in the engagement folder.
- Impact stated without exaggeration or copied data.
- Detection note written: what log or alert should fire.
- Fix is specific, owned, and testable.

COMMON MISTAKE: Describing a finding only as a tool result. A tool name is not impact. Write what could be reached and what should change.

HANDS-ON EXERCISE
Scenario: In the official lab, you have written scope for two lab machines and a training app. Decide on paper first.
Decision point 1: The application uses a documented default credential. Correct path: Log in once, screenshot proof without changes, log out, and report it as critical.
Decision point 2: A lab account can read a folder outside its role. Correct path: Record the path and permissions, open nothing beyond the listing, and report the flaw.
Decision point 3: A tool suggests testing a machine outside lab scope. Correct path: Refuse and note it as untested.

KNOWLEDGE CHECK
[CHECK]
Q: What is the professional stopping point when testing a weakness?
A: When you reach the highest possible privilege
B: When you have proved the finding at the minimum level needed
C: When the tool finishes its full run
ANSWER: B
FEEDBACK: Proof, not maximum access, is the goal. Pushing to highest privilege adds damage and data risk without adding evidence the client can act on.
[/CHECK]
[CHECK]
Q: Which defense directly addresses password guessing and reuse?
A: Longer server names
B: Hiding the login page
C: Unique passwords with multi-factor authentication and login alerting
D: More administrator accounts
ANSWER: C
FEEDBACK: Unique passwords stop reuse, multi-factor authentication blocks a guessed password alone, and alerting exposes repeated failures. Hiding the login page fails because nothing limits guessing once it is found.
[/CHECK]
[CHECK]
Q: In post-exploitation documentation, what matters most about sensitive data?
A: Copying it fully so the client believes you
B: Recording that it was reachable, under the rules, without keeping it beyond the agreement
C: Moving it to your own storage for safekeeping
ANSWER: B
FEEDBACK: The finding is reachability and the condition that allowed it. Copying or keeping client data fails the rules and creates a second breach risk in your own files.
[/CHECK]

KEY TAKEAWAYS
- Start from a confirmed finding, not a tool menu
- Prove each weakness minimally, then stop
- Each flaw class has a clear defensive signal to report
- Post-exploitation records reachability; it does not collect client data
- Every finding needs impact, detection, and a specific fix

GLOSSARY
Exploitation — Testing whether a weakness can be used, under authorization
Privilege escalation — Gaining higher privileges than an account should have
Default credential — A vendor-set password that was never changed
Least privilege — Giving each account only the access its role requires
Post-exploitation — Assessing what proved access can reach

FURTHER READING
- CompTIA PenTest+: https://www.comptia.org/certifications/pentest
- INE eJPT: https://ine.com/certifications/ejpt-certification

CERTIFICATION ALIGNMENT
Supports: CompTIA PenTest+ (PT0-003) — attacks and exploits domain; eJPT (INE) — host and network penetration testing domains.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
