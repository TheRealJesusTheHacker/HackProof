Routing & Switching Essentials

MODULE OVERVIEW
Level: Beginner to Intermediate | Time: 90 minutes | Prerequisites: Networking fundamentals.

LEARNING OBJECTIVES
After this module you can:
- Explain how switches and routers move traffic
- Describe VLANs and trunking and why networks use them
- Compare static and dynamic routing
- Explain NAT, DHCP, and DNS as core IP services
- Apply port security and first-hop security basics

LESSON 1 — SWITCHING, VLANS, AND TRUNKING
A switch moves traffic inside one local network, learning which device sits on which port by hardware address. A router moves traffic between networks by IP address, using its routing table. Most access problems are switching problems; most problems reaching another site are routing problems. Naming the layer is the first troubleshooting step.

A VLAN is a logical network inside a switch. Devices in different VLANs cannot talk directly even on the same switch; traffic must pass through a router or Layer 3 switch, where policy applies. Offices separate staff, guests, phones, and cameras so a fault in one does not reach all. A trunk carries several VLANs between switches, tagging frames. An access port carries one VLAN. A device in the wrong VLAN looks dead when the network is doing what it was told.

CASE BREAKDOWN: A new camera shows no connection, though cable and camera test good. Its port was set to the staff VLAN, while cameras belong in the camera VLAN, the only one allowed to reach the recorder. Moving the port restores it in minutes. No hardware was faulty.

Procedure — placing a device on a network:
1. Identify which VLAN the device class belongs to.
2. Set the port as an access port in that VLAN.
3. Confirm the device received an address in the right range.
4. Test one service it should reach, and one it should not.

COMMON MISTAKE: Putting every device in one VLAN because it is simpler. A single security problem then reaches the whole site.

LESSON 2 — ROUTING, IP SERVICES, AND FIRST-HOP SECURITY
Static routing means you enter each path by hand. It is predictable and suits a small site with one exit. Dynamic routing means routers exchange paths and adjust when a link fails; it scales, but needs design and monitoring. Choose static for simple networks and dynamic where paths must fail over. Every router also needs a default route.

Three IP services appear at every site. DHCP assigns addresses; when devices lose them, check DHCP before cabling. DNS turns names into addresses; when services work by address but not by name, suspect DNS. NAT lets many private addresses share one public address; when a site loses internet but local traffic works, suspect NAT and the WAN link.

Security starts at the first hop. Port security limits which hardware addresses may use a port, so an unknown device on a wall jack does not join. DHCP snooping and dynamic ARP inspection, at concept level, stop a rogue device from handing out addresses or impersonating the gateway. Disable unused ports. Automation awareness: automation multiplies both correct designs and mistakes, so learn the concepts first.

CASE BREAKDOWN: Branch users reach local shares but no websites; names fail while a known public address answers. WAN and NAT are healthy. The branch DNS setting points to a server retired the previous week. Correcting the DNS address handed out by DHCP restores service.

Checklist — first-pass troubleshooting:
- Is the fault inside one VLAN, or between networks?
- Did the device get a correct address, gateway, and DNS?
- Does the service answer by address? By name?
- What changed last on that switch, router, or service?

COMMON MISTAKE: Replacing hardware before testing by address and by name. That comparison separates switching, routing, and DNS faults.

HANDS-ON EXERCISE
Scenario: In a lab you control, a PC in the guest VLAN reaches the internet but also a lab file server it should not. Decide on paper first.
Decision point 1: The server is also in the guest VLAN from an old lab setup. Correct path: Move the server to its intended VLAN and retest reachability and isolation.
Decision point 2: After the move, the PC cannot reach the server at all, including an allowed service. Correct path: Check routing and access rules between the VLANs; isolation should block general access, not the approved service.
Decision point 3: A second PC on the same wall jack joins freely. Correct path: Enable port security on that port, disable unused ports, and retest.

KNOWLEDGE CHECK
[CHECK]
Q: A device in the wrong VLAN appears completely dead, though its cable tests good. Why?
A: VLANs block all traffic permanently
B: The port is forwarding as designed, but for a network the device does not belong to
C: Switches cannot support cameras
ANSWER: B
FEEDBACK: Switching follows configuration, not intention, so a wrong VLAN isolates a healthy device. The permanent-block option fails because moving the port to the correct VLAN restores service at once.
[/CHECK]
[CHECK]
Q: Services answer by IP address but not by name. What do you suspect first?
A: NAT
B: Port security
C: DNS
D: Trunking
ANSWER: C
FEEDBACK: Name failure with working addresses is the classic DNS signature. NAT fails because address-based traffic is already crossing the network.
[/CHECK]
[CHECK]
Q: When is static routing the better choice?
A: In a small, stable network with one exit path
B: In a large network with many backup paths
C: Never, because it cannot fail over manually
ANSWER: A
FEEDBACK: Static routes are simple and predictable where paths are few and stable. Large multi-path networks fail with them because every failover needs a manual edit.
[/CHECK]

KEY TAKEAWAYS
- Switches move traffic inside a network; routers between networks
- VLANs separate traffic by design; trunks carry several VLANs
- Static routing suits small sites; dynamic routing suits failover
- Test by address and by name to separate routing from DNS
- Port security and disabled ports protect the first hop

GLOSSARY
VLAN — A logical network inside a switch, separated from others
Trunk — A link carrying several VLANs between switches, frames tagged
Routing table — Paths a router uses to forward traffic between networks
NAT — Translating private addresses to a shared public address
DHCP — Assigns addresses and settings automatically
Port security — Limits which hardware addresses may use a port

FURTHER READING
- Cisco CCNA: https://www.cisco.com/site/us/en/learn/training-certifications/certifications/enterprise/ccna/index.html

CERTIFICATION ALIGNMENT
Supports: Cisco CCNA (200-301) — network fundamentals, IP connectivity, IP services, and security fundamentals domains; orientation toward CCNP for senior roles.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
Readiness material is preparation guidance, not a guarantee of any exam result.
