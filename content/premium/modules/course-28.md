Networking Fundamentals
MODULE OVERVIEW
Level: Beginner | Time: 90 minutes | Prerequisites: Basic computer use.

LEARNING OBJECTIVES
After this module you can:
- Explain the OSI and TCP/IP models in plain terms and place tasks in them
- Read an IP address, subnet mask, and gateway, and work a subnetting example
- Name the ports and protocols behind web, email, and DNS traffic
- Choose cabling and a topology for a small network
- Secure a home or small-office wireless network

LESSON 1 — MODELS, ADDRESSES, AND SUBNETTING WITHOUT THE MYSTERY
Models are maps. OSI has seven layers, bottom to top: Physical (cables), Data Link (switches, MAC addresses), Network (IP, routers), Transport (TCP/UDP), Session, Presentation, Application (your programs). TCP/IP compresses this to four: Link, Internet, Transport, Application. Troubleshoot bottom-up: no link light is layer 1; Wi-Fi connected but no websites can be layer 3 or DNS.
Every device needs an IP address, subnet mask, and usually a gateway. In 192.168.1.10/24, the first three numbers are the network, the last is the host. Devices sharing the network part talk directly; anything else goes to the gateway.
Worked example: split 192.168.1.0/24 into two /25 networks for staff and guests. Each half has 126 usable addresses: .1-.126 and .129-.254. Borrow one bit, halve the block. Private ranges (10.x, 172.16-31.x, 192.168.x) are internal only; the router translates them to one public address via NAT.
Ports label services: 80 HTTP, 443 HTTPS, 53 DNS, 67/68 DHCP, 25 SMTP, 993 IMAP, 3389 RDP, 22 SSH. TCP confirms delivery (web, files); UDP does not wait (calls, DNS) and is faster for it.
CASE BREAKDOWN: Illustrative walkthrough — a printer is hand-set to 192.168.2.50 on a 192.168.1.0/24 network. Jobs vanish without errors: the network part differs, so PCs send jobs to the gateway, which cannot deliver them. It could have stopped at address checking. The signal most people miss: an "almost the same" IP is a different network, not a near miss.
Addressing checklist:
1. Write IP, mask, and gateway side by side.
2. Confirm network parts match locally.
3. Confirm the gateway is in the same subnet.
4. Check for duplicate addresses.
COMMON MISTAKE: Setting a static address inside the DHCP pool with no reservation, so the router hands it to another device too.

LESSON 2 — CABLING, TOPOLOGIES, AND SECURE WIRELESS
Wired Ethernet uses twisted-pair cable: Cat5e handles gigabit on typical runs; Cat6 gives more headroom. Runs are limited to about 100 metres; damage and poor terminations cause faults that come and go. Fibre carries light over long distances, immune to electrical interference. Most small networks are a star: every device to a central switch, so one failed cable drops one device. That switch is a single point of failure — keep a spare for critical sites.
Wireless: 2.4 GHz reaches farther but is slower and crowded; 5 GHz is faster, shorter range. Place access points centrally and high. Baseline: WPA3 or WPA2-AES — never WEP or open; long, unique Wi-Fi password; change the default admin password; WPS off; firmware updated; guests and gadgets on a guest network.
Worked example: a cafe till shares a network with customer Wi-Fi. Put customers on the guest network, keep the till private, and test that a guest phone cannot see the office PC.
CASE BREAKDOWN: Illustrative walkthrough — a home worker's video calls freeze every afternoon, yet wired speed tests are fine. The router sits behind a TV in a corner, on a channel a neighbour's network crowds after school. Moving it central and changing channel ends it. It could have stopped with a survey before buying a faster plan. The signal most people miss: fast wired tests plus bad Wi-Fi means a radio problem, not the internet service.
Small-network checklist:
1. Router central and elevated.
2. WPA3/WPA2-AES, unique passwords, WPS off.
3. Firmware updated; guest network on.
4. Label both ends of every cable.
COMMON MISTAKE: Buying a faster plan for a coverage problem. Bandwidth does not fix distance or a crowded channel.

HANDS-ON EXERCISE
Work on paper, using your router's admin pages only to look.
Decision point 1: The router has its factory admin password, though the Wi-Fi password is strong. Leave it? Correct path: No. The admin password controls every setting, including Wi-Fi.
Decision point 2: A smart TV and work laptop share one network; a guest network is available. Correct path: TV and gadgets on guest, laptop on private; test that guest devices cannot see it.
Decision point 3: A printer needs a fixed address; the pool is .100-.199. Correct path: Reserve it, or set a static address outside the pool such as .50, and record it.

KNOWLEDGE CHECK
[CHECK]
Q: In 192.168.1.10/24, which part identifies the network?
A: The last number only
B: The first three numbers, 192.168.1
C: The /24 identifies one device
ANSWER: B
FEEDBACK: A /24 mask means the first three numbers are the network, the last is the host — why a .2.x printer on a .1.x network is unreachable.
[/CHECK]
[CHECK]
Q: Sites load by IP address but not by name. Likely service at fault?
A: Cabling at the physical layer
B: DNS, port 53
C: The monitor
ANSWER: B
FEEDBACK: Loading by IP proves addressing and routing work; failing by name points to DNS. Cabling is tempting, but the link is demonstrably up.
[/CHECK]
[CHECK]
Q: Which wireless settings are the secure baseline?
A: WEP, default admin password, WPS on
B: An open network with a welcome page
C: WPA3 or WPA2-AES, unique passwords, WPS off, firmware updated
ANSWER: C
FEEDBACK: WEP and open networks offer no real protection and WPS is easily attacked. The baseline is modern encryption, unique credentials, WPS off, current firmware.
[/CHECK]

KEY TAKEAWAYS
- Use the model; troubleshoot bottom-up, do not guess
- IP, mask, and gateway must agree; network parts must match locally
- Know the core ports: 443, 53, 67/68, 993, 3389, 22
- Star topology contains failures; know your single points of failure
- Segment guests and gadgets; WPA3, unique passwords, WPS off

GLOSSARY
Subnet mask — Value splitting an IP address into network and host
Default gateway — Router address devices use to reach other networks
NAT — Translation letting many private addresses share one public
TCP — Delivery-checked transport used by web, email, and files
UDP — Fast, unconfirmed transport used by calls, streaming, and DNS
WPA3 — Current Wi-Fi encryption standard; WPA2-AES is the fallback

FURTHER READING
CompTIA Network+ exam objectives: https://www.comptia.org
Cisco networking basics: https://www.cisco.com
CISA guidance on securing home networks: https://www.cisa.gov

CERTIFICATION ALIGNMENT
Supports: CompTIA Network+ (N10-009) — networking concepts and networking implementation domains.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately through the certification body.
