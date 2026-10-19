Identity, Access & Security Architecture
MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Threats & Cryptography.

LEARNING OBJECTIVES
After this module you can:
- Explain identification, authentication, authorisation, and accounting
- Rank MFA methods by strength for a stated risk
- Explain SSO and federation and the risk they concentrate
- Describe zero trust in plain terms and apply it
- Use segmentation, redundancy, and hardening to limit damage by design

LESSON 1 — IDENTITY AND ACCESS: WHO ARE YOU, WHAT MAY YOU DO
Identity has four steps. Identification: claim an identity (a username). Authentication: prove it — password (know), token (have), biometrics (are). Authorisation: what that identity may do. Accounting: actions logged to it. Least privilege: only the access the job needs, only as long as needed. Shared accounts break accounting; standing admin rights break least privilege.
MFA means two different factor types. Strength order: SMS codes (SIM-swap risk), app codes (better, still phishable), push approvals (prompt fatigue), hardware keys or passkeys (strongest, phishing-resistant). Worked example: a SIM swap defeats a finance user's SMS codes; a hardware key gives an attacker nothing — it will not authenticate to a fake site.
SSO lets one sign-in reach many services; federation extends that trust across organisations. Both concentrate risk at the identity provider, which needs your strongest MFA and monitoring.
CASE BREAKDOWN: Illustrative walkthrough — a departed contractor's account stays active for months. Their old password, reused and exposed elsewhere, is tried by an outsider and works; the account still holds file-server access. It could have stopped at offboarding: disable access on the last day. The signal most people miss: dormant accounts are unmonitored — nobody notices their misuse.
Access checklist:
1. Unique account per person; no shared logins.
2. MFA on email, remote access, admin, and finance accounts first.
3. Least privilege by role; review access on a schedule.
4. Disable accounts the day someone leaves.
5. Log sign-ins; review the logs.
COMMON MISTAKE: Giving everyone admin "to avoid support calls." Every compromised account becomes a full compromise.

LESSON 2 — ZERO TRUST AND ARCHITECTURE THAT LIMITS DAMAGE
Zero trust in plain terms: stop trusting a user or device just because it is inside your network. Verify identity and device health for each access, grant the minimum, assume an attacker may already be inside. Working parts: strong identity, segmentation, continuous checking.
Segmentation divides a network into zones with controlled crossings: PCs, servers, guest Wi-Fi, and cameras should not all reach each other. Example: on a flat network, ransomware on a reception PC reaches the file server in minutes; segmented, it stalls in its zone.
Redundancy removes single points of failure: a second internet link, backups in a separate location, a spare switch. Hardening shrinks what a system offers: remove unused software and services, change default passwords, apply secure baselines, patch on schedule, disable legacy protocols.
CASE BREAKDOWN: Illustrative walkthrough — an office keeps cameras, PCs, and its server on one flat network. A camera with a default password is found from the internet and used as a foothold to reach the server's shares. It could have stopped at design: cameras on their own segment cannot initiate server connections, and a changed default password closes the entry. The signal most people miss: cheap connected devices are computers too, usually the least patched.
Architecture checklist:
1. Draw the zones; list what may cross, and why.
2. Keep guests, cameras, and gadgets outside data zones.
3. Find single points of failure; add redundancy there.
4. Harden: defaults changed, unused services off, patching scheduled.
5. Confirm backups are separate and restore-tested.
COMMON MISTAKE: Buying security tools for a flat network. Segmentation and identity decide how far an attacker gets.

HANDS-ON EXERCISE
Paper exercise for a network you own.
Decision point 1: An office has PCs, a server, guest Wi-Fi, and cameras on one network. First change? Correct path: Segment — guests and cameras in their own zones, no route to the server.
Decision point 2: The owner wants one shared front-desk login to save time. Correct path: Decline and explain accounting: unique accounts take minutes, and a shared login makes every action unattributable.
Decision point 3: One upgrade: an off-site backup copy, or a bigger firewall you will not configure. Correct path: The off-site backup — redundancy for irreplaceable data beats unconfigured features.

KNOWLEDGE CHECK
[CHECK]
Q: Which MFA method is strongest for a high-risk admin account?
A: SMS codes to a mobile phone
B: A hardware security key or passkey
C: Security questions about the user
ANSWER: B
FEEDBACK: Hardware keys are phishing-resistant and cannot be SIM-swapped. SMS is tempting because it is easy, but numbers can be transferred.
[/CHECK]
[CHECK]
Q: Zero trust, in plain terms, means:
A: No employee is trusted personally
B: Trust is never granted by network location; verify identity and grant the minimum each time
C: All traffic must go through a VPN
ANSWER: B
FEEDBACK: Zero trust removes implicit trust from being "inside." A VPN alone still grants broad access once connected.
[/CHECK]
[CHECK]
Q: Ransomware reaches the file server fastest in which design?
A: A segmented network where PC zones cannot open server connections
B: A flat network where every device can reach every other device
C: A network with offline backups
ANSWER: B
FEEDBACK: On a flat network nothing slows lateral movement. Segmentation contains the same attack to one zone.
[/CHECK]

KEY TAKEAWAYS
- Identification, authentication, authorisation, accounting: separate steps
- MFA strength: hardware keys and passkeys above apps, apps above SMS
- SSO and federation concentrate risk at the identity provider
- Zero trust: verify, grant the minimum, assume breach
- Segmentation, redundancy, and hardening decide how much one incident costs

GLOSSARY
Authorisation — What a proven identity is allowed to do
MFA — Two different factor types to prove identity
Passkey — Phishing-resistant credential using a key pair
Federation — One organisation vouching for its users to another
Segmentation — Network zones with controlled crossings
Hardening — Reducing attack surface by removing the unused

FURTHER READING
CompTIA Security+ objectives: https://www.comptia.org
NIST Zero Trust Architecture (SP 800-207): https://www.nist.gov
CISA MFA guidance: https://www.cisa.gov

CERTIFICATION ALIGNMENT
Supports: CompTIA Security+ (SY0-701) — Domain 3 (security architecture) and Domain 1 identity and access concepts.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately through the certification body.
