Computer Hardware Essentials
MODULE OVERVIEW
Level: Beginner | Time: 75-90 minutes | Prerequisites: None.

LEARNING OBJECTIVES
After this module you can:
- Name each major PC component and explain what it does
- Match cables and connectors to devices without forcing a wrong fit
- Compare storage, RAM, and display choices for a stated need
- Decide whether to build, buy prebuilt, or upgrade, and why
- Apply the six-step troubleshooting methodology to a hardware fault

LESSON 1 — INSIDE THE BOX: WHAT EACH PART DOES
The CPU executes instructions: more cores help with many tasks at once, faster clocks help single tasks finish sooner. The motherboard connects everything and sets compatibility — which CPU, RAM, and storage fit. RAM is short-term workspace: open programs live there and clear when power goes off. Storage is long-term keeping; an SSD has no moving parts and is far faster than a spinning drive, so a drive swap often makes an old PC feel new. The PSU converts wall power to what parts need; a failing PSU causes random shutdowns that mimic other faults. A GPU renders images; office work can use CPU graphics, gaming and 3D need a dedicated card. Fans remove heat; dust and blocked vents cause shutdowns.
Connectors: HDMI and DisplayPort carry video; USB-C can carry data, video, and power; SATA connects drives; RJ45 is Ethernet. Never force a connector.
CASE BREAKDOWN: Illustrative walkthrough — an office PC shuts down mid-afternoon but runs fine mornings. The owner swaps PSU, then RAM, with no change. A technician asks when it happens: the PC sits in sun, vent against a wall. Heat builds until the CPU shuts down to protect itself. Moving and cleaning it ends the fault. It could have stopped at identifying the pattern before swapping parts. The signal most people miss: faults tied to time of day usually mean heat or power, not a dead part.
Hardware triage checklist:
1. Note what fails, when, and what changed recently.
2. Check power, cables, vents, and visible damage first.
3. Test one known-good part at a time.
4. Record each change and result.
COMMON MISTAKE: Swapping several parts at once. If the fault clears you learn nothing, and a new fault cannot be traced to one part.

LESSON 2 — BUILD, BUY, OR UPGRADE, AND THE SIX STEPS
Build when you need a specific mix and accept being your own warranty desk. Buy prebuilt when uptime and one warranty matter most. Upgrade when the base is sound: an SSD or more RAM extends a working PC's life for far less than replacement. Decide in order: state the job, set a total budget, check compatibility, compare cost and downtime.
CompTIA's six-step methodology: 1) Identify the problem — gather information, question the user, note recent changes. 2) Establish a theory of probable cause, simplest first. 3) Test the theory; if it fails, form a new one or escalate. 4) Establish a plan of action and note side effects. 5) Implement the solution or escalate. 6) Verify full functionality, add preventive measures, and document findings, actions, and outcomes.
Worked example — no image: fans spin; the desk was moved yesterday (identify). Theory: cable in the wrong port. Test: it is in the motherboard port, but a GPU is fitted. Implement: move it to the GPU port. Verify and document: image returns.
CASE BREAKDOWN: Illustrative walkthrough — a trainee orders a motherboard for a PC that will not power on. A mentor makes him work the steps. Identifying the problem, he learns the PC worked until a power strip was replaced during cleaning. Testing the simplest theory, power delivery, he finds the strip switched off. The PC starts at once. It could have stopped at theory stage: power outranks boards. The signal most people miss: "worked until it was moved or cleaned" is a cause clue, not small talk.
No-power checklist, in order:
1. Is the wall outlet live? Test it with a charger.
2. Strip on and not tripped? Cable seated both ends? PSU switch on?
3. Any lights, fans, or sounds? Note them exactly.
4. Only then open the case, power unplugged, with static precautions.
COMMON MISTAKE: Skipping documentation. The next fault gets diagnosed from zero.

HANDS-ON EXERCISE
Use a PC you own, or work on paper.
Decision point 1: A PC with 8 GB RAM and a spinning drive is slow to boot and open programs. Buy a new CPU? Correct path: No. Boot and load delays point to storage; an SSD addresses the symptom for less.
Decision point 2: You add a second monitor; GPU and monitor both offer DisplayPort. Correct path: Use that matching pair instead of an adapter chain.
Decision point 3: After fitting the SSD the PC will not boot. Reinstall everything? Correct path: No. Identify the change, test cable seating and BIOS boot order, then act on what the test shows.

KNOWLEDGE CHECK
[CHECK]
Q: A PC is slow to boot and open programs but fine once loaded. Which upgrade most directly helps?
A: A larger monitor
B: Replacing the hard drive with an SSD
C: A higher-wattage power supply
ANSWER: B
FEEDBACK: Boot and load times are storage-bound, so an SSD is the direct fix. More PSU wattage is tempting but does not speed loading.
[/CHECK]
[CHECK]
Q: What follows establishing a theory of probable cause in the six steps?
A: Documenting the outcome
B: Implementing the costliest fix
C: Testing the theory to determine the cause
ANSWER: C
FEEDBACK: Test before you act. Skipping the test leads to swapped parts, new faults, and no proof of what was wrong.
[/CHECK]
[CHECK]
Q: A PC will not power on after a desk move. Check first:
A: Power delivery — outlet, strip, cables, PSU switch
B: Replace the motherboard
C: Replace the CPU
ANSWER: A
FEEDBACK: After a move, power and cabling are the simplest, most likely causes. Board replacement skips the method.
[/CHECK]

KEY TAKEAWAYS
- CPU thinks, RAM is workspace, storage keeps; map the symptom to the right part
- Compatibility starts at the motherboard; never force a connector
- SSD and RAM upgrades revive a sound PC for less than replacement
- Work the six steps in order and document every fix
- Change one thing at a time and record the result

GLOSSARY
CPU — Processor that executes program instructions
RAM — Short-term workspace memory that clears when power goes off
SSD — Solid-state storage with no moving parts, far faster than a hard drive
Motherboard — Main board connecting all parts and setting compatibility
PSU — Power supply converting wall power for components
GPU — Graphics unit that renders images to a display

FURTHER READING
CompTIA A+ exam objectives and certification: https://www.comptia.org
Microsoft Windows and PC support: https://learn.microsoft.com

CERTIFICATION ALIGNMENT
Supports: CompTIA A+ Core 1 (220-1101) — hardware, networking basics, and hardware and network troubleshooting domains.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
