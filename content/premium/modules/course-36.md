Pen Test Engagements: Reporting & Lab Strategy

MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Ethical Hacking Methodology; Exploitation Basics.

LEARNING OBJECTIVES
After this module you can:
- Plan an engagement from first call to final report
- Write scope, agreements, and rules of engagement
- Keep notes that support every finding
- Write findings a business owner can act on
- Run a lab plan for hands-on exams

LESSON 1 — THE ENGAGEMENT LIFECYCLE
Authorization rule: test only with written permission from the system owner, for the systems and time window named in it. No signed agreement and no scope means no testing. Practice only on systems you own or in official labs.

An engagement runs in a fixed order. Planning: agree the goal, scope, exclusions, timing, and contacts. Legal agreements: a contract and authorization signed by someone with authority over the systems, plus a non-disclosure agreement where required. Rules of engagement: allowed and prohibited techniques, data handling, and escalation. Testing: only inside those documents. Reporting: findings, evidence, and fixes. Closure: remove test accounts as agreed, confirm it, and debrief.

Note-taking runs through all of it. Use one folder and timestamps on every note and screenshot. Write for a reader who was not there: target, action, result, and why it matters, recorded the same hour.

CASE BREAKDOWN: A tester reports a serious flaw from memory, with no timestamped evidence. The client cannot match it to their logs and asks for a retest. A second tester's identical finding, backed by dated notes, is accepted and fixed the same week.

Procedure — starting an engagement:
1. Confirm signed authorization, scope, and rules before any scan.
2. Create the engagement folder and notes template.
3. Log the kickoff: contacts, escalation path, window.
4. Record every action with time, target, and result.

COMMON MISTAKE: Starting technical work while the contract is still being drafted. Goodwill is not authorization.

LESSON 2 — FINDINGS THAT GET FIXED, AND LAB STRATEGY
A finding an owner can act on has five parts: a plain title, what you found with evidence, business impact, an honest view of likelihood and seriousness, and a specific fix with an owner. Translate tool output: state what could be reached, which data is affected, and what to change first. Order by business risk, not test order.

Lab strategy is the same discipline. PNPT and OSCP are hands-on exams earned in proctored labs; this module is preparation guidance only. Practice in official labs and systems you own. Survey everything first, note every lead, then work in time blocks. Set a rule before you start: if a path yields no new evidence after a focused block, log it and move on. Review failed sessions for process errors, not only technical gaps.

CASE BREAKDOWN: In practice labs, a candidate spends most of a session on one hard machine, with no notes on the others and no new evidence for most of that time. Next session she time-boxes each lead and rotates, finishing with complete notes on every machine. Her time discipline changed, not her knowledge.

Checklist — before you submit a report or finish a lab session:
- Every finding has evidence, impact, and a fix.
- No finding depends on memory or an unsaved screenshot.
- Lab notes list what was tried, even where it failed.
- Your next session starts from the log, not recall.

COMMON MISTAKE: Writing the report for other testers. The reader who approves the fix is an owner. If they cannot tell what to do first, the report failed.

HANDS-ON EXERCISE
Scenario: In an official practice lab, you have ninety minutes to turn a sample finding into a report entry and a study plan. Decide on paper.
Decision point 1: The evidence is a screenshot with no timestamp or target. Correct path: Do not report it yet. Reproduce it in the lab, save it with time and target, and note the steps.
Decision point 2: Your draft title uses only a scanner code. Correct path: Rewrite it stating the problem, impact, and affected system.
Decision point 3: In a timed session, one lead has produced nothing for a full work block. Correct path: Log what you tried, move to the next lead, and return only if time remains.

KNOWLEDGE CHECK
[CHECK]
Q: What must be in place before testing starts on an engagement?
A: A kickoff call and a verbal agreement to proceed
B: Signed authorization, defined scope, and agreed rules of engagement
C: A scanner profile ready to run
ANSWER: B
FEEDBACK: Signed documents are the legal basis and operating limits of the test. A verbal agreement fails because scope, authority, and data handling are undocumented and easily disputed.
[/CHECK]
[CHECK]
Q: Which finding title is most useful to a business owner?
A: A scanner reference code and severity number
B: A list of the tools used during testing
C: Plain language stating the problem, impact, and affected system
D: The name of the weakness class only
ANSWER: C
FEEDBACK: Owners approve fixes, so they need the problem and its impact in plain terms. A scanner code fails because it requires the reader to decode it before they can act.
[/CHECK]
[CHECK]
Q: In a timed hands-on lab, a lead has produced no new evidence for a full work block. What is the disciplined move?
A: Stay on it until it breaks, however long that takes
B: Log what you tried and move to the next lead
C: Restart the whole session from zero
ANSWER: B
FEEDBACK: Time-boxing protects the whole attempt, and the log preserves work for a later return. Staying indefinitely fails because effort on one lead starves every other lead.
[/CHECK]

KEY TAKEAWAYS
- Signed authorization, scope, and rules come before any test
- Notes taken the same hour are evidence; later ones are summary
- A finding needs impact and a specific fix an owner can approve
- Hands-on exams reward survey, time-boxing, and logs
- Report by business risk, not test order

GLOSSARY
Rules of engagement — Agreed limits, contacts, and prohibited actions
Finding — A documented weakness with evidence, impact, and a fix
Scope — Written list of systems and activities in an engagement
Time-boxing — A fixed work block for a lead before rotating
Debrief — Closing review of findings and next steps with the client

FURTHER READING
- CompTIA PenTest+: https://www.comptia.org/certifications/pentest
- TCM Security PNPT: https://tcm-sec.com/
- OffSec OSCP: https://www.offsec.com/courses/pen-200/

CERTIFICATION ALIGNMENT
Supports: CompTIA PenTest+ (PT0-003) — engagement management and reporting and communication domains; readiness orientation for TCM PNPT and OffSec OSCP, which are hands-on exams earned in proctored labs — preparation guidance only.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
Readiness material is preparation guidance, not a guarantee of any exam result.
