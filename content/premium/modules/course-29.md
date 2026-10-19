Network Operations & Troubleshooting
MODULE OVERVIEW
Level: Intermediate | Time: 90 minutes | Prerequisites: Networking Fundamentals.

LEARNING OBJECTIVES
After this module you can:
- Explain what DHCP, DNS, and VPNs do and where each fails
- Set a baseline and use simple monitoring to spot change early
- Keep documentation and policies a new technician can use
- Apply a structured method to "the network is down"
- Decide when to fix, escalate, or roll back a change

LESSON 1 — THE SERVICES EVERY NETWORK RUNS ON
DHCP hands out addresses for a lease period. A device that gets no lease often self-assigns a 169.254.x.x address and reaches nothing: service down, pool exhausted, wrong segment. DNS turns names into addresses; when it fails, connections by IP still work — compare a lookup with a direct IP connection. A VPN is an encrypted tunnel across an untrusted network; its faults are usually credentials, expired certificates, or a clash where home and office both use 192.168.1.0/24.
Also recognise: NTP keeps clocks in sync — wrong clocks break logins and certificates.
Operations means knowing normal. A baseline is a snapshot taken when things work: typical bandwidth, latency to key systems, device counts, error rates. Monitoring compares live values with it, so "slow since Tuesday" becomes a graph, not an argument. Keep alerts few and acted on.
CASE BREAKDOWN: Illustrative walkthrough — every Monday at 9 a.m. an office reports "the network is down" for twenty minutes, and rebooting the router becomes the ritual. A baseline shows the DHCP pool is exhausted as phones, laptops, and visitors arrive at once. Enlarging the pool ends the fault. It could have stopped when someone counted addresses instead of rebooting. The signal most people miss: faults that follow a schedule follow a resource — leases, backups, or capacity.
Service check, in order:
1. Addressing: real IP, mask, gateway, DNS?
2. Names: does a lookup return the right address?
3. Path: gateway, then external IP, then a name?
4. Service: is the app or VPN up for others?
COMMON MISTAKE: Rebooting first. It clears the evidence, and the fault returns with no data.

LESSON 2 — DOCUMENTATION, POLICY, AND "THE NETWORK IS DOWN"
Documentation that earns its keep: a labelled diagram, an inventory, an IP register, and a change log (what, when, who, why, rollback). Keep it reachable during an outage — a diagram only on the down file server helps no one. Policies: acceptable use, device access, guest access, and a change process — announced, tested, reversible.
The method for "the network is down": 1) Define scope before touching anything — one user, floor, site, or everyone? One app or everything? 2) Check shared points: power, device lights, line status, any change in the last 24 hours. 3) Test in layers: gateway, external IP, name lookup. 4) Form the smallest theory that fits the scope, test it, fix or roll back. 5) Verify with the reporters, monitor, and log the cause.
Worked example: one floor loses access; other floors are fine. Its switch shows no lights — the power feed was unplugged and the UPS battery is exhausted. Restoring power fixes it; the socket is labelled and logged.
CASE BREAKDOWN: Illustrative walkthrough — after a Friday firewall change, a site cannot reach its cloud accounting app on Monday. The change log shows a cleanup "removed unused rules"; one removed rule carried that traffic. Rolling it back restores service in minutes. It could have stopped at change review: deleting rules without checking what used them. The signal most people miss: "broke after a change" means suspect the change first.
Outage checklist:
1. Record time, reporter, symptoms.
2. State the scope: who, where, what.
3. Check power, lights, line status, recent changes.
4. Test gateway, external IP, DNS, in that order.
5. Give users a status and next update time.
COMMON MISTAKE: Everyone fixing at once with no log. Changes collide and nobody can say what worked.

HANDS-ON EXERCISE
Home lab or paper scenario: the household reports "the internet is down" while a video call on one laptop still works.
Decision point 1: Is the network down? Correct path: No — scope is partial. One working device proves the line and router live; find what differs on the failing devices.
Decision point 2: Failing devices show 169.254 addresses. Correct path: Check DHCP first — those addresses mean leases failed. Check the DHCP page and pool size before restarting anything.
Decision point 3: Restarting the router restores service, cause unknown. Correct path: Log time and symptoms, start a simple baseline, and watch for recurrence instead of declaring it solved.

KNOWLEDGE CHECK
[CHECK]
Q: A device shows a 169.254.x.x address and reaches nothing. What failed?
A: DNS name resolution
B: It could not obtain a DHCP lease
C: The VPN tunnel dropped
ANSWER: B
FEEDBACK: 169.254 addresses are self-assigned when DHCP gives no lease. A DNS failure leaves a normal address and IP connections working.
[/CHECK]
[CHECK]
Q: Sites load by IP address but not by name. Where do you look?
A: Replace the router
B: DNS settings and the DNS service, port 53
C: Re-cable the office
ANSWER: B
FEEDBACK: Working by IP proves the path; failing by name isolates DNS. Replacing hardware skips that layered test.
[/CHECK]
[CHECK]
Q: Why keep a baseline when everything works?
A: It is only needed for audits
B: Monitoring works fine without one
C: It lets you prove what changed when performance departs from normal
ANSWER: C
FEEDBACK: A baseline turns "it feels slower" into comparable numbers. Without one, investigations start from opinion.
[/CHECK]

KEY TAKEAWAYS
- DHCP, DNS, and VPN failures each have a recognisable signature; test for it
- A 169.254 address means no lease; name-only failure means DNS
- Baselines turn complaints into evidence; alert only on actionable change
- Define scope before touching anything in an outage
- Keep diagram, inventory, address register, and change log reachable in an outage

GLOSSARY
DHCP — Service assigning IP configuration for a lease period
DNS — Service translating names to IP addresses
VPN — Encrypted tunnel carrying private traffic across an untrusted network
Baseline — Recorded snapshot of normal performance used for comparison
NTP — Service keeping device clocks synchronised
Change log — Record of what changed, when, by whom, and its reversal

FURTHER READING
CompTIA Network+ exam objectives: https://www.comptia.org
Cisco network operations topics: https://www.cisco.com
Microsoft networking documentation: https://learn.microsoft.com

CERTIFICATION ALIGNMENT
Supports: CompTIA Network+ (N10-009) — network operations and network troubleshooting domains; orientation toward Cisco CCNA operational thinking.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately through the certification body.
