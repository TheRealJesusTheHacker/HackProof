Ethical Hacking Methodology

MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Networking and OS fundamentals.

LEARNING OBJECTIVES
After this module you can:
- Explain the five phases of ethical hacking and the purpose of each
- Define scope and rules of engagement before testing begins
- Describe what defenders detect at each phase
- Document work during testing for the final report
- Stop work outside written authorization

LESSON 1 — AUTHORIZATION FIRST, THEN THE FIVE PHASES
Authorization rule: test only with written permission from the system owner, for the systems and time window named in it. No written permission and no defined scope means no testing. If a target's status is unclear, stop and ask in writing. Practice only on systems you own or in official labs.

Phase 1, Reconnaissance: gather information from permitted sources — published material, public records, DNS. Defenders watch for unusual query volume.
Phase 2, Scanning: identify live hosts, open ports, and services in scope. Defenders watch firewall and detection logs.
Phase 3, Gaining Access: at methodology level, assess whether a known weakness in an in-scope service could allow access, using only allowed methods. Defenders watch for failed logins and unexpected processes.
Phase 4, Maintaining Access: test whether lawfully gained access would persist, and record how, so the client can close it. Defenders watch for new accounts and unusual outbound connections.
Phase 5, Covering Tracks: in authorized work you never erase evidence to hide from the client. Study how attackers remove logs so you can advise on logging that defeats it.

CASE BREAKDOWN: A tester finds a staging server linked from a client's site but not in scope. She does not scan it. The client confirms in writing that it is theirs and adds it to scope, and only then does she test it. Testing out of scope could have cost the engagement and her legal protection.

Procedure — before you run any tool:
1. List in-scope addresses and exclusions from the signed authorization.
2. Confirm the window, emergency contact, and action if production degrades.
3. Record your source address for log correlation.
4. Start a notes file: date, time, tool, target, result.
5. Confirm prohibited actions, such as denial-of-service tests.

COMMON MISTAKE: Treating verbal permission from an employee as authorization. Only written permission from someone with authority over the systems protects you.

LESSON 2 — RULES OF ENGAGEMENT AND WHAT DEFENDERS SEE
Rules of engagement are the written operating limits: scope, timing, allowed and prohibited techniques, data handling, evidence storage, contacts, and how fast you report a critical finding. Agree them before testing and carry them during testing.

Separate passive gathering from active probing in your notes. Expect scanning to be logged; state when you scanned so the client can match your activity to alerts. Use the minimum needed to prove a finding, then stop and document.

CASE BREAKDOWN: A tester proves a file server allows broader access than intended by opening one sample file. He stops, records the path and permissions, and reports the same day instead of opening the full archive, which the rules prohibited and which would have added no proof.

Checklist — closing each phase:
- Notes timestamped and saved in the engagement folder.
- Every system touched has a result or a no-finding entry.
- Out-of-scope discoveries reported, not tested.
- Critical findings escalated via the agreed contact.

COMMON MISTAKE: Reconstructing work at report deadline. Notes taken during testing are evidence; later notes are a summary at best.

HANDS-ON EXERCISE
Scenario: The official lab gives you a written scope naming two virtual machines you own. Work the decisions on paper first.
Decision point 1: A third machine appears on the lab network, unnamed in scope. Correct path: Do not scan it. Record it, notify the instructor, and work only the named systems.
Decision point 2: A scan of an in-scope host shows more services than expected. Correct path: Record each service, check it against the rules, and assess in order of business relevance.
Decision point 3: You prove a weakness and could push deeper. Correct path: Stop at proof, save evidence and timestamps, and write the finding.

KNOWLEDGE CHECK
[CHECK]
Q: What must exist before any ethical hacking test begins?
A: A verbal go-ahead from any employee at the target
B: Written permission from the system owner with defined scope and time window
C: A scan showing the target is reachable
D: A signed invoice for the work
ANSWER: B
FEEDBACK: Written authorization with defined scope is the legal basis for testing. A verbal go-ahead fails because that employee may lack authority over the systems and nothing is documented.
[/CHECK]
[CHECK]
Q: In an authorized engagement, how should you treat the covering tracks phase?
A: Erase logs so the client cannot see what you did
B: Skip it, because it has no defensive value
C: Study how attackers hide activity so you can advise on logging and retention
ANSWER: C
FEEDBACK: In authorized work you account for your actions, you do not hide them. Erasing logs destroys the evidence your report and the client's detection depend on.
[/CHECK]
[CHECK]
Q: Mid-test, you find a linked server that is not in scope. What do you do?
A: Test it, since the client would obviously want it covered
B: Stop, do not test it, and seek written confirmation to add it to scope
C: Test it lightly and mention it only if you find something
ANSWER: B
FEEDBACK: Scope is a written boundary, not an assumption. Light testing fails for the same reason full testing does: no authorization exists until the client adds it in writing.
[/CHECK]

KEY TAKEAWAYS
- Written authorization and defined scope come before any tool
- The five phases give a repeatable, defensible structure
- Defenders log every phase, so timestamped notes protect everyone
- Prove a finding minimally, then stop and document
- Out-of-scope discoveries are reported, never tested alone

GLOSSARY
Scope — Written list of systems and activities in an engagement
Rules of engagement — Agreed limits, contacts, and prohibited actions for a test
Reconnaissance — Gathering information from permitted sources
Enumeration — Listing services, users, or resources found on a target
Evidence — Saved output and notes supporting a reported finding

FURTHER READING
- EC-Council CEH: https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/
- INE eJPT: https://ine.com/certifications/ejpt-certification

CERTIFICATION ALIGNMENT
Supports: CEH (EC-Council) — introduction to ethical hacking, footprinting and reconnaissance, scanning, and enumeration modules; eJPT (INE) — assessment methodologies domain.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
