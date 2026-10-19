# 03 — Tech Support Calls: Hang Up

## Module Overview

**Level:** Foundations
**Time:** 20 minutes
**Prerequisites:** None

The scam: someone calls claiming to be Microsoft, Apple, or your "security team." Your computer sent "error reports." They will "fix" it — if you give them access and pay. The same script arrives as a pop-up with a phone number. This module walks the script, shows the trick used as "proof," and gives you one rule that ends every version.

**LEARNING OBJECTIVES — After this module you can:**

- Recognize the script's four steps
- Explain why Event Viewer warnings are normal
- State who never cold-calls you
- End a call or pop-up correctly
- Act correctly if you gave access or paid

## Lesson 1: The Script

1. **The hook.** "Your PC is infected." "Your license expired." "Illegal activity on your IP." The claim changes; the pressure does not. You are told of a problem you cannot see or check.
2. **The proof.** They walk you to the Windows Event Viewer and show warnings and errors, calling them "viruses." Every Windows computer shows these — a normal log of routine notices. See Lesson 2.
3. **The access.** "Install this remote tool so I can fix it." Once you do, they are inside your computer: moving the mouse, opening files, showing staged "evidence" while other work happens off-screen.
4. **The payment.** A fee by gift cards, wire, or card — or the "refund" turn: they "accidentally" send too much and ask for the difference back. The refund was never real, so what you send is your own money, gone.

### Case Breakdown: The Pop-Up

**What happened:** Rosa's screen freezes under a warning: "Windows security alert. Your computer is locked. Call support now. Do not restart." She calls. The "technician" has her open Event Viewer, gasps at the warnings, and takes remote access. She pays in gift cards.

**Where it could have stopped:** At the pop-up. Microsoft and Apple never put a phone number in a warning, and a pop-up cannot lock your computer — closing the browser ends it.

**The signal most people miss:** The instruction not to restart. A real warning survives one. This one does not, and the sender knows it — restarting breaks the stage set.

### What to Say — Script

- To any cold caller: **"I don't take support calls I didn't make. I'm hanging up now."** Then hang up. Do not argue — the caller has a rehearsed answer for every fact.
- If a pop-up gives a number: do not call it. Close the browser; if it will not close, restart.
- Worried afterward? Call the company's real number yourself, from its official site.

> **COMMON MISTAKE:** Staying on the line to be polite. Time is the caller's whole strategy — and hanging up costs you nothing if you are wrong.

## Lesson 2: The Truth

- **Nobody monitors your home PC.** Microsoft and Apple do not call you. Ever. Neither does your provider's "security team."
- Real support never cold-calls, never asks for remote access out of nowhere, and never takes gift cards. A request for gift cards or wire is not a payment method — it is the diagnosis.
- **Event Viewer warnings are normal noise.** Windows logs them constantly, on healthy machines, by design. An entry records something routine — a delayed service, a retry — not an infection. The same screen appears on a brand-new computer.
- "Your IP was flagged" is meaningless. They don't know your IP; they're dialing thousands of numbers, and no caller can see your files through one.

### Case Breakdown: The Refund

**What happened:** After paying once, Tom gets a second call: the "company is closing" and will refund him. On screen, he watches his bank balance jump. Told too much was sent, he wires back the difference. The "refund" was a transfer staged between his own accounts.

**Where it could have stopped:** At the premise. A company that took gift cards is not refunding his bank — and a refund never requires you to send money first.

**The signal most people miss:** The balance was real — the movement was between his own accounts. Real numbers, false story.

### The Rule

**Hang up.** Worried? Call the company's real number yourself, from its official site.

**If you gave access:** disconnect from the internet, have the machine professionally cleaned, change passwords typed since then from a clean device, and call your bank if you paid.

> **COMMON MISTAKE:** Testing the caller with questions only a "real technician" would know. The script anticipates them. The test is who started the contact — if they contacted you, it fails.

## Hands-On Exercise

Your phone rings. "This is Microsoft security. Your computer sent us error reports. We must check it now or your internet will be disconnected."

**Decision point 1:** He names a real company. Does that clear him? No — naming Microsoft costs nothing, and the claim cannot be checked, by design.
**Decision point 2:** He asks you to open Event Viewer "just to look." Harmless? No. That is step 2; the warnings are already on every machine.
**Decision point 3:** Say the script line, hang up, and call Microsoft yourself from its official site if still worried.

**Correct path:** End the call. No access, no payment, nothing installed.

## Knowledge Check

**1. A pop-up says your computer is locked and gives a number. What do you do?**
A. Call it — a locked computer is an emergency
B. Close the browser or restart; never call that number
C. Pay the fee shown so it unlocks
D. Let the caller check Event Viewer first

**2. A caller shows you dozens of Event Viewer warnings. What do they prove?**
A. Your computer is infected
B. Hackers have been active on your machine
C. Nothing — warnings like these are normal on healthy computers
D. Your license has expired

**3. You gave a caller remote access and paid by gift card. What now?**
A. Wait; the access ended with the call
B. Call the same number and demand a refund
C. Disconnect the machine, change passwords from a clean device, have it professionally cleaned, and call your bank
D. Delete the remote tool and carry on

### Answer Key

**1. B.** Microsoft and Apple never show pop-up phone numbers. A fails because the "lock" is a browser page — restarting ends it, which is why the pop-up forbids it.
**2. C.** Event Viewer logs routine warnings on every machine. A fails because the same screen appears on a healthy, new computer.
**3. C.** Assume passwords typed since the access are burned. A fails because tools can outlast the call; B is this scam's second act.

## Key Takeaways

- Microsoft, Apple, and your provider do not cold-call you. Nobody monitors your home PC.
- Event Viewer warnings are normal noise — evidence of nothing.
- Remote access plus gift cards, wire, or a repayable "refund" is the scam, in that order.
- Hang up. Worried? Call the real number yourself, from the official site.
- Never call a number shown in a pop-up.

## Glossary

**Cold call** — A call you did not request, started by the other party.
**Event Viewer** — A built-in Windows log of routine notices, warnings, and errors.
**Remote access tool** — Software letting another person see and control your computer.
**Pop-up** — A window appearing over your screen, here used to stage a fake warning.
**Gift card payment** — Paying with gift card numbers; untraceable, which is why scammers demand it.
**IP address** — Your connection's network address, not your identity.

## Further Reading

- FTC: https://consumer.ftc.gov
- Report fraud: https://reportfraud.ftc.gov
- FBI IC3: https://www.ic3.gov

## Certification alignment

**Supports:** CompTIA Security+ (SY0-701) Domain 2 — vishing and pretexting.

Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
