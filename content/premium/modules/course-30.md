Threats, Vulnerabilities & Cryptography
MODULE OVERVIEW
Level: Intermediate | Time: 90 min | Prerequisites: Networking.

LEARNING OBJECTIVES
After this module you can:
- Describe threat actors, their motives, and their vectors
- Distinguish malware types by what they do and how they spread
- Explain vulnerability, exploit, and exposure in plain terms
- Choose symmetric, asymmetric, or hashing for a stated job
- Explain what certificates, PKI, and TLS do in a connection

LESSON 1 — ACTORS, VECTORS, MALWARE, AND VULNERABILITIES
Threat actors differ by motive. Organised crime wants money: ransomware, fraud, stolen data. Nation-state actors want long-term access and information. Insiders hold legitimate access, so their risk is misuse or error. Most breaches start with ordinary vectors — phishing, an unpatched flaw, a reused password, misconfiguration.
Malware by behaviour: a virus attaches to files; a worm spreads by itself; a trojan hides a payload in something legitimate; ransomware encrypts files for payment; a RAT gives an attacker control; a keylogger records typing.
A vulnerability is a weakness — a flaw, a missing patch, a weak setting; an exploit is the method used against it. Example: a router flaw is minor if that service is off, urgent if it is internet-exposed and a public exploit exists. Context decides priority.
CASE BREAKDOWN: Illustrative walkthrough — a firm is hit by ransomware on a Monday. An employee opened an invoice attachment Friday; attackers returned over the weekend through remote access protected only by a reused password. It could have stopped twice: attachment caution, and unique passwords with MFA. The signal most people miss: the quiet gap between entry and damage, when detection limits it to one machine.
Suspected infection checklist:
1. Disconnect the machine from the network; do not power it off unless told to.
2. Note the time, what was opened, and any message shown.
3. Warn IT or your security contact at once; delete nothing.
4. Do not pay or run "cleanup" downloads from search results.
COMMON MISTAKE: Treating phishing as an IT problem only. Reporting a suspicious email fast is a security control.

LESSON 2 — CRYPTOGRAPHY THAT MATTERS, IN PLAIN TERMS
Encryption scrambles data so only a key holder can read it. Symmetric encryption uses one shared key: fast, used for files and the bulk of a web session; its problem is sharing that key safely. Asymmetric encryption uses a key pair — public key shared, private key secret. What the public key locks, only the private key unlocks. Slower, so systems use it briefly to agree a symmetric key, then switch.
Hashing turns data into a fixed, one-way fingerprint. Uses: storing passwords (hashed and salted, never plain) and proving a file unchanged. Worked example: compare a download's published SHA-256 hash with yours. Match means as published; mismatch means stop.
Certificates and PKI tie keys to identities: a certificate states a public key belongs to a named site, signed by an authority your browser trusts. In TLS the browser checks it, both sides agree a fresh symmetric key, and the session runs encrypted. TLS protects data in transit; it does not prove a site honest.
CASE BREAKDOWN: Illustrative walkthrough — an employee on cafe Wi-Fi sees a certificate warning on a banking site, clicks through, and signs in. The connection was intercepted; the warning was the one control that worked. It could have stopped there: close the page and use a trusted network. The signal most people miss: certificate warnings are rare and specific — dismissing them removes TLS's identity check.
Crypto decision guide:
1. Stored data or bulk traffic: symmetric.
2. Agree a secret with a stranger, or sign: asymmetric.
3. Prove data unchanged, store a password: hashing (salted for passwords).
4. Prove a website's identity: its certificate.
COMMON MISTAKE: Storing the encryption key beside the data it protects — an attacker gets both at once.

HANDS-ON EXERCISE
Safe home exercises only.
Decision point 1: Create a text file, calculate its SHA-256 hash, change one character, and hash again. Correct path: The fingerprints differ completely — the integrity check working, and why a mismatch on a real download means stop.
Decision point 2: A site shows a certificate warning and a colleague says to click through. Correct path: Do not. Close the page; use a trusted network.
Decision point 3: You must send a sensitive document to a partner. Correct path: Agree the encrypted method and key exchange through a separate channel first; a key sent in the same email protects nothing.

KNOWLEDGE CHECK
[CHECK]
Q: Why do real systems combine asymmetric and symmetric encryption?
A: Symmetric alone is illegal for web use
B: Asymmetric solves safe key agreement; symmetric is fast for the bulk data
C: Hashing replaces both in TLS
ANSWER: B
FEEDBACK: Asymmetric methods agree a key with a stranger but are slow, so TLS uses them briefly, then switches to symmetric. Hashing checks integrity; it does not encrypt.
[/CHECK]
[CHECK]
Q: A downloaded file's SHA-256 hash does not match the published value. You should:
A: Install it anyway; hashes are approximate
B: Stop and treat the file as altered or wrong until explained
C: Rename the file and retry
ANSWER: B
FEEDBACK: A hash is an exact fingerprint; any change gives a different value. There is no "close enough."
[/CHECK]
[CHECK]
Q: An HTTPS padlock on a website proves:
A: The site is honest and its content is safe
B: The connection is encrypted and the certificate matches the named site
C: The site has never been breached
ANSWER: B
FEEDBACK: TLS protects the connection and checks the identity named in the certificate. A phishing site can hold a valid certificate for its own name.
[/CHECK]

KEY TAKEAWAYS
- Most attacks start with phishing, unpatched flaws, or reused passwords
- Name malware by behaviour; find the entry point first
- Vulnerability plus exploit plus exposure sets urgency
- Symmetric is fast; asymmetric agrees keys; hashing proves integrity
- TLS encrypts the connection; it does not certify a site honest

GLOSSARY
Threat actor — Group behind an attack
Vector — Route an attack takes, such as phishing
Vulnerability — A weakness that can be exploited
Hashing — One-way fingerprinting used to prove integrity
PKI — Certificates and authorities tying keys to identities
TLS — Protocol encrypting web connections

FURTHER READING
CompTIA Security+ objectives: https://www.comptia.org
NIST cryptography publications: https://www.nist.gov
CISA phishing and ransomware guidance: https://www.cisa.gov

CERTIFICATION ALIGNMENT
Supports: CompTIA Security+ (SY0-701) — Domain 1 (general security concepts, including cryptographic solutions) and Domain 2 (threats, vulnerabilities, mitigations).
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — exams are taken separately through the certification body.
