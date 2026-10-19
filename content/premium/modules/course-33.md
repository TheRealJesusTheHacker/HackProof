Threat Intelligence & Vulnerability Management
MODULE OVERVIEW
Level: Intermediate | Time: 90 min | Prerequisites: Security Operations.

LEARNING OBJECTIVES
After this module you can:
- Name the main threat intelligence sources and their uses
- Turn intelligence into a concrete check or defence change
- Explain a CVSS score in plain terms and its limits
- Run a scan and work a remediation workflow to closure
- Report a finding to a non-technical owner clearly

LESSON 1 — THREAT INTELLIGENCE AN ANALYST CAN USE
Threat intelligence is organised information about attackers, used to make a decision. Sources: government advisories (CISA alerts, its Known Exploited Vulnerabilities catalog) show what is exploited now; your own logs show what touches your systems; feeds supply indicators — malicious addresses, domains, hashes — for tools to block. Levels: strategic (trends), operational (campaigns), tactical (indicators).
Use it as a loop, not a subscription. An advisory says a remote-access flaw is exploited. Step 1: Do we run it? Check the inventory. Step 2: Exposed — version, internet-facing? Step 3: Patch, mitigate, or monitor. Step 4: Hunt logs for its indicators. An advisory producing no action was reading, not intelligence.
CASE BREAKDOWN: Illustrative walkthrough — an alert about a flaw in a provider's software sits in a shared mailbox for two weeks; nobody owned advisories. Attackers find the unpatched system in days. It could have stopped at ownership: a named reviewer, a set day, a ticket. The signal most people miss: "we get the alerts" is not a control.
Intelligence checklist:
1. Name who reviews advisories, and when.
2. Match each item against the asset inventory.
3. Open a ticket for anything you run and cannot rule out.
4. Hunt logs for its indicators; record the result.
COMMON MISTAKE: Collecting feeds nobody reads. One owned source beats five ignored ones.

LESSON 2 — SCANNING, CVSS, AND FIXING IN THE RIGHT ORDER
Vulnerability scanning checks systems against known weaknesses. Authenticated scans sign in and see patch levels in depth; unauthenticated scans see the outsider's view. A scan produces findings, not priorities.
CVSS scores a vulnerability 0-10 by exploitability and impact on confidentiality, integrity, and availability: 9-10 Critical, 7-8.9 High, 4-6.9 Medium, below 4 Low. Adjust for context: in CISA's exploited catalog? Internet-facing? Worked example: a Critical flaw on an isolated test machine can wait behind an exploited High flaw on your internet-facing email system. Score orders the list; context re-orders it.
Remediation workflow: scan on schedule, validate findings, assign owner and deadline by priority, patch or mitigate, rescan to verify, and record exceptions formally with an expiry date. Report in decision language: the flaw in one plain sentence, what could happen, your recommendation, downtime cost, deadline. Example: "A flaw in our remote-access system lets an outsider in without a password, and attackers are using it now. Patch tonight; about an hour down."
CASE BREAKDOWN: Illustrative walkthrough — a scan reports 400 findings and the owner approves none. An analyst regroups: 6 are internet-facing and exploited, 40 high internally, the rest batch monthly. The 6 are approved that day. It could have stopped at presentation: a scanner dump is not a decision document. The signal most people miss: owners refuse unreadable decisions, not risk ones.
Remediation checklist:
1. Validate the finding; rule out false positives.
2. Score it; adjust for exposure and exploitation.
3. Assign owner and deadline; patch, mitigate, or accept with expiry.
4. Rescan to verify; report in plain language.
COMMON MISTAKE: Chasing the highest CVSS first while an exploited, exposed High waits.

HANDS-ON EXERCISE
Paper exercise.
Decision point 1: Critical 9.8 on an offline test PC; High 8.1, actively exploited, on your internet-facing VPN. Correct path: The VPN first — exploitation plus exposure beats a higher score on an isolated machine.
Decision point 2: A scanner flags a missing patch that checking shows is installed, on a disabled service. Correct path: Record a validated false positive with evidence; do not open a fix ticket.
Decision point 3: An owner chooses between patching tonight or next week. Correct path: Present decision language — the flaw, attacker activity, downtime cost, your recommendation and deadline — and record the decision.

KNOWLEDGE CHECK
[CHECK]
Q: An intelligence advisory arrives about a flaw in a product you run, internet-facing. First correct action:
A: File it for the quarterly review
B: Check your version and exposure, open a tracked ticket, and hunt logs for its indicators
C: Wait to see if other firms are breached
ANSWER: B
FEEDBACK: Intelligence counts only when it becomes a check and an action. Filing it leaves the exposure running.
[/CHECK]
[CHECK]
Q: A High CVSS flaw is actively exploited on your internet-facing system; a Critical flaw sits on an isolated test machine. Patch order:
A: Critical first, always — the score decides
B: The exploited, exposed High first; context re-orders the score
C: Neither until the next scan
ANSWER: B
FEEDBACK: CVSS cannot know your exposure. Active exploitation plus internet reachability is the higher real risk.
[/CHECK]
[CHECK]
Q: The best way to report a finding to a non-technical owner is:
A: Send the full scanner output so nothing is hidden
B: State the flaw, the risk, the recommendation, the cost, and the deadline in plain language
C: Give only the CVSS number; it speaks for itself
ANSWER: B
FEEDBACK: Owners decide when the choice is readable. A raw dump buries it; a bare score has no cost or deadline.
[/CHECK]

KEY TAKEAWAYS
- Intelligence is only real when it triggers a check, a hunt, or a fix
- Own your advisories: a named reviewer, set days, tracked tickets
- CVSS orders findings; exposure and active exploitation re-order them
- Validate, assign, patch or formally accept, then rescan to prove closure
- Report in decision language: risk, recommendation, cost, deadline

GLOSSARY
Threat intelligence — Information about attackers used to decide defences
Indicator — Observable sign of attack, such as a malicious domain
CVSS — Score rating a vulnerability's severity, 0 to 10
False positive — A finding that checking shows is not real
Compensating control — Safeguard offsetting a risk not yet fixed
KEV catalog — CISA's list of known-exploited vulnerabilities

FURTHER READING
CISA KEV catalog and alerts: https://www.cisa.gov
CompTIA CySA+ objectives: https://www.comptia.org
FIRST CVSS documentation: https://www.first.org

CERTIFICATION ALIGNMENT
Supports: CompTIA CySA+ (CS0-003) — threat intelligence, vulnerability management, and reporting and communication domains; Security+ Domain 5 supporting.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately.
