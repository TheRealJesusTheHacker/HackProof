Security Operations & Incident Response
MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Identity, Access & Security Architecture.

LEARNING OBJECTIVES
After this module you can:
- Walk the incident response cycle in order, with each phase's goal
- Triage an alert using scope, evidence, and business impact
- Explain which logs matter and what a good entry gives you
- Contain an incident without destroying needed evidence
- Run lessons learned that produces owned, dated changes

LESSON 1 — THE RESPONSE CYCLE AS A WORKED PLAYBOOK
Incident response has seven phases. Preparation: plans, contacts, tools, and backups, before anything happens. Detection: an alert or user report says something may be wrong. Analysis: confirm it is real, what is affected, and how serious it is. Containment: stop the spread — isolate a machine, disable an account — without yet fixing the cause. Eradication: remove the attacker's access and the entry point. Recovery: restore from known-good sources, patch, and monitor as systems return. Lessons learned: document and change what failed.
Worked playbook — ransomware on a workstation at 09:10. Detection: the user calls, an alert fires. Analysis (09:20): one machine, no spread yet. Containment (09:25): disconnect it, disable the user's sessions. Eradication: entry was a malicious attachment; remove it, reset credentials. Recovery: rebuild from a clean image, restore pre-incident backups, verify, reconnect, watch for days. Lessons learned: review filtering and reporting time.
CASE BREAKDOWN: Illustrative walkthrough — a firm rebuilds an infected server within an hour and declares success. Two days later the attacker returns through the same unpatched remote-access service — unidentified, because the rebuild destroyed the logs showing the entry point. It could have stopped at analysis: preserve evidence, and close the entry, not just the machine. The signal most people miss: unanswered "how did they get in" guarantees a repeat.
Containment checklist:
1. Isolate affected machines; note the time.
2. Preserve evidence: logs, the malicious file, screenshots.
3. Disable compromised accounts and sessions.
4. Tell the incident lead what you did, in writing.
COMMON MISTAKE: Reimaging first. It destroys the evidence identifying the entry point.

LESSON 2 — LOGGING, MONITORING, AND ALERT TRIAGE
You cannot analyse what you did not record. Logs that matter: sign-ins (success and failure) for email, VPN, and admin systems; firewall and DNS activity; endpoint and audit logs. A useful entry has a synchronised timestamp, account, device, action, and result. Centralise logs where an attacker who owns one machine cannot delete them, and keep clocks in sync (NTP) or timelines fall apart.
Triage decides what deserves a responder now. Three questions: Is it real — does a second source agree? Scope — one machine or many, admin account, data involved? Impact if true? The same alert on a reception PC and the backup server are different incidents. Real, spreading, or high-value: contain first. Low impact: record, watch, set a review time.
CASE BREAKDOWN: Illustrative walkthrough — an analyst works 200 overnight alerts top-down. Alert 187, a sign-in to a dormant account from an unusual address, waits until morning — by which time data has been copied out. Triage by scope and value ranks it first. It could have stopped at triage order. The signal most people miss: attackers aim for quiet alerts; volume is not severity.
Triage procedure:
1. Group duplicates; note first and last time seen.
2. Corroborate with a second source.
3. Rank by account value, scope, and data — not arrival order.
4. Assign: act now, watch with a deadline, or close with a reason recorded.
COMMON MISTAKE: Closing alerts to clear the queue. An unexplained closure is a blind spot.

HANDS-ON EXERCISE
Tabletop exercise on paper only.
Decision point 1: An alert reports malware on one workstation; the user confirms a strange attachment was opened. Correct path: Contain now — isolate the machine, preserve evidence. Waiting is the risky option.
Decision point 2: The user's account signed in from two locations an hour apart. Correct path: Treat it as compromised — disable sessions, reset credentials, check what it touched.
Decision point 3: Leadership wants the incident closed today. Correct path: Close operations, but schedule lessons learned with owners and dates, and keep heightened monitoring for an agreed period.

KNOWLEDGE CHECK
[CHECK]
Q: Which phase comes immediately before eradication, and why does the order matter?
A: Recovery, so users return fastest
B: Containment, so spread stops before you remove the cause
C: Lessons learned, to assign blame early
ANSWER: B
FEEDBACK: Containment stops the spread first; eradicating while an attacker still spreads wastes the cleanup. Recovery first invites reinfection.
[/CHECK]
[CHECK]
Q: Two alerts arrive: malware on a reception PC, and a dormant admin account signing in from an unusual location. Triage first:
A: The reception PC, because malware sounds worse
B: Whichever arrived first
C: The dormant admin sign-in, because account value and stealth raise its impact
ANSWER: C
FEEDBACK: Triage ranks by value, scope, and stealth, not arrival order. A quiet privileged sign-in can mean data loss under way.
[/CHECK]
[CHECK]
Q: Why centralise logs off the machines that generate them?
A: It makes logs prettier for reports
B: An attacker who owns a machine cannot delete central copies, preserving evidence
C: Local logs are illegal to keep
ANSWER: B
FEEDBACK: Local-only logs vanish in exactly the incidents you need them for. Central copies survive for analysis.
[/CHECK]

KEY TAKEAWAYS
- Work the cycle in order: prepare, detect, analyse, contain, eradicate, recover, learn
- Contain before you clean; preserve evidence before you rebuild
- Logs need synchronised time, identity, action, and a safe central home
- Triage by value, scope, and stealth — never by arrival order
- Lessons learned ends with owned, dated changes, not a discussion

GLOSSARY
Containment — Limiting spread before removing the cause
Eradication — Removing attacker access and the entry point
Triage — Ranking alerts by impact to set response order
SIEM — System collecting and correlating logs centrally
Playbook — Pre-agreed steps for a defined incident type
Lessons learned — Review producing corrective changes

FURTHER READING
CompTIA Security+ and CySA+ objectives: https://www.comptia.org
NIST Incident Handling Guide (SP 800-61): https://www.nist.gov
CISA incident response guidance: https://www.cisa.gov

CERTIFICATION ALIGNMENT
Supports: CompTIA Security+ (SY0-701) Domain 4 (security operations); CySA+ (CS0-003) incident response (orientation).
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately.
