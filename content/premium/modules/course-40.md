Cloud Administration & Security

MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Cloud Foundations.

LEARNING OBJECTIVES
After this module you can:
- Administer identities in Entra ID and AWS IAM
- Organize resources for ownership, policy, and cost
- Apply network and policy controls
- Set up logging and review it for security events
- Describe endpoint management scope

LESSON 1 — IDENTITIES, RESOURCES, AND ENDPOINTS
Administration starts with identity. Microsoft Entra ID, formerly Azure AD, holds users and groups for Azure and Microsoft 365. AWS IAM holds users, roles, and policies. Every person signs in as themselves, administrators use separate accounts, access is granted by group or role at least privilege, and temporary access beats permanent access. Require multi-factor authentication and review access on a schedule.

Organize resources so ownership is never a question. In Azure, resources sit in resource groups inside subscriptions; in AWS, accounts sit in an organization. Tag resources with owner and purpose. Endpoint management is the companion discipline: Microsoft Intune, the scope of MD-102, enrolls devices, applies policy, and can wipe a lost device.

CASE BREAKDOWN: A departing contractor's account is disabled, but a later review finds an access key under it still active, with broad rights. The sign-in was closed; the credential was not. The fix is a leaver checklist removing accounts, keys, role assignments, and sessions together.

Procedure — granting access:
1. Confirm the business need and exact resources.
2. Grant by group or role, at least privilege, with an expiry where possible.
3. Require multi-factor authentication.
4. Record owner, reason, and review date.
5. Remove access at review if the need ended.

COMMON MISTAKE: Granting permanent administrator rights for one task. The task ends in an hour; the rights remain for years unless a review removes them.

LESSON 2 — SECURITY CONTROLS, GOVERNANCE, AND COST
Network controls decide what reaches a resource. Azure network security groups and AWS security groups allow or deny traffic by address and port. Default to closed: open only the ports a service needs, from only the sources that need them. A database should not accept internet connections because a rule was copied from a web server.

Policy turns intentions into enforced rules. Azure Policy and AWS service control policies can require tags, block public storage, or restrict regions. Logging makes security real: enable Azure Monitor and AWS CloudTrail, store logs where one compromised account cannot erase them, and review alerts on a schedule. Encrypt data at rest and in transit.

Governance and cost are the same habit. Budgets with alerts stop quiet growth. A monthly review covers untagged resources, unused high privilege, and anything nobody can explain; unexplained items get an owner and a date, or removal.

CASE BREAKDOWN: An auditor asks who owns a storage account holding client exports. No tag names an owner, and its rule allows public access from an old project. The team cannot prove the exposure period because logs were never retained. Remediation: owner tags by policy, public access blocked, logs retained, monthly review.

Checklist — monthly review:
- Access: remove stale users, keys, and high privileges.
- Resources: every resource tagged and owned.
- Network: no public rule without a named need.
- Cost and logs: budgets, alerts, and retention confirmed.

COMMON MISTAKE: Turning on logging during an incident. Logs record forward from enablement. Enable them on day one and test reading them.

HANDS-ON EXERCISE
Scenario: On paper, you inherit a cloud account with no tags, one shared administrator login, and storage open to the internet. Sequence the fixes.
Decision point 1: The team wants to keep the shared administrator login. Correct path: Create named accounts, require multi-factor authentication, separate admin accounts, and retire the shared login.
Decision point 2: The public storage rule might belong to an old project. Correct path: Close public access until an owner proves the need in writing.
Decision point 3: Logging was never enabled, and leadership asks for last quarter's activity. Correct path: State that it cannot be reconstructed, enable logging and retention now, and record the gap.

KNOWLEDGE CHECK
[CHECK]
Q: What is the correct way to grant a colleague access for one defined task?
A: Permanent administrator rights, removed when someone remembers
B: The shared administrator login, for speed
C: Access by group or role at least privilege, with a review date
ANSWER: C
FEEDBACK: Group or role access at least privilege is scoped, recorded, and reviewable. A shared login fails because actions cannot be attributed to a person.
[/CHECK]
[CHECK]
Q: A database accepts connections from the internet through a copied web server rule. What is the flaw class?
A: Excessive network exposure from an unreviewed rule
B: Insufficient logging retention
C: Missing resource tags
D: Weak password policy
ANSWER: A
FEEDBACK: The database is reachable from sources that should never reach it, because a rule was reused without review. Logging and tags do not create or fix the exposure itself.
[/CHECK]
[CHECK]
Q: When must cloud logging be enabled to help in an incident?
A: During the incident, once you know what to look for
B: On day one, with retention, before any incident
C: Only for administrator accounts
ANSWER: B
FEEDBACK: Logs record forward from enablement, so day-one logging with retention is the only way history exists. Enabling during an incident misses the events you need.
[/CHECK]

KEY TAKEAWAYS
- Identity first: named accounts, least privilege, reviews
- Groups, roles, and tags prove it
- Network rules default to closed, open only on a named need
- Policy enforces; logging proves what happened
- Monthly review joins access, resources, and cost

GLOSSARY
Entra ID — Microsoft identity service for Azure and Microsoft 365
IAM — AWS identity and access management
Least privilege — Only the access a job requires
Network security group — Rules allowing or denying traffic to resources
CloudTrail — AWS log of account activity for audit
Intune — Microsoft endpoint management for devices

FURTHER READING
- Microsoft AZ-104: https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/
- AWS Security Specialty: https://aws.amazon.com/certification/certified-security-specialty/

CERTIFICATION ALIGNMENT
Supports: Microsoft AZ-104 (orientation) — identity, governance, monitoring; MD-102 (orientation) — endpoint management; AZ-500 and AWS Certified Security — Specialty (awareness: advanced exams taken separately).
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
Readiness material is preparation guidance, not a guarantee of any exam result.
