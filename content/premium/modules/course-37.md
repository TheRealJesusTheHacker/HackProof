Linux System Administration Essentials

MODULE OVERVIEW
Level: Beginner to Intermediate | Time: 90 minutes | Prerequisites: Basic computer use.

LEARNING OBJECTIVES
After this module you can:
- Navigate the filesystem and explain its main directories
- Manage users, groups, and file permissions
- Install and update software with a package manager
- Manage services and read logs to find faults
- Use core shell commands and troubleshoot methodically

LESSON 1 — FILESYSTEM, USERS, AND PERMISSIONS
Linux organizes everything under a single root directory, written as /. Key locations: /home holds user folders, /etc holds configuration, /var holds logs and changing data, /usr holds programs, and /tmp holds temporary files. Move with cd, list with ls, and print your location with pwd. Learn absolute paths, which start at /, and relative paths, which start where you are.

Every file has an owner, a group, and permissions for owner, group, and others: read, write, and execute. View them with ls -l, change them with chmod, and change ownership with chown. Manage accounts with useradd, usermod, and passwd. Privilege is granted through sudo, which runs one command with administrator rights and logs it. Give sudo only to accounts that need it.

CASE BREAKDOWN: A junior admin makes a shared folder writable by everyone so a team can save files quickly. A week later, a script in that folder is altered by an unrelated account. The fix: set group ownership, grant the group write access, and remove access for others. The shortcut saved five minutes and created the incident.

Procedure — creating a user and a shared folder:
1. Create the account and set a password the user must change.
2. Confirm the correct group and add the account.
3. Set the folder's group ownership and permissions.
4. Confirm others have no unneeded access.
5. Log in as the user and test reading and writing.

COMMON MISTAKE: Fixing a permission error by granting access to everyone. That removes the error and the protection together. Fix the owner or group instead.

LESSON 2 — PACKAGES, SERVICES, LOGS, AND TROUBLESHOOTING
Package managers install software from trusted repositories and track dependencies. On Debian-based systems use apt; on Red Hat-based systems use dnf. Apply updates on a planned cycle, remove software you no longer need, and record what you changed and when.

Services are background programs managed by systemd. Start, stop, enable, and check them with systemctl, and read their state before you change it. Logs live under /var/log and through journalctl. When something fails, read the log for that service and time first; the error is usually recorded.

Troubleshoot in a fixed order: define the symptom, check the service, check recent changes, read the relevant log, check disk and permissions, test one fix at a time, and record the result. Shell essentials support this: pipes send one command's output to another, grep searches text, and a script is a saved list of commands run in order. Never run a script you do not understand with administrator rights.

CASE BREAKDOWN: A file server stops sharing files after a weekend. The admin checks the service, finds it failed, and reads its log: an old backup filled the disk. He removes the expired backup, restarts the service, and confirms users can connect. Method, not reinstalling, found the cause.

Checklist — methodical troubleshooting:
- State the symptom and when it started.
- Check service status and recent changes.
- Read the matching log before changing settings.
- Change one thing, test it, and record it.

COMMON MISTAKE: Changing several settings at once. If the fault clears, you do not know which change fixed it, and you cannot undo cleanly.

HANDS-ON EXERCISE
Scenario: In a Linux virtual machine you own, a test service will not start and a teammate cannot write to a shared folder.
Decision point 1: The folder denies your teammate's account. Correct path: Check owner, group, and permissions with ls -l, fix the group, and test as that account.
Decision point 2: The service shows failed status. Correct path: Read its journal entries for the failure time before changing any configuration.
Decision point 3: The log shows the disk is full. Correct path: Identify what filled it, remove only what you can confirm is expired, then restart and test the service.

KNOWLEDGE CHECK
[CHECK]
Q: A teammate cannot write to a shared folder. What is the correct first fix to try?
A: Grant write access to everyone
B: Check the folder's owner, group, and permissions, then fix the group access
C: Delete and recreate the folder
D: Give the teammate administrator rights
ANSWER: B
FEEDBACK: Most write failures are an owner or group problem, fixed precisely. Granting everyone access fails because it removes the protection permissions exist to provide.
[/CHECK]
[CHECK]
Q: A service will not start. What should you read first?
A: The logs for that service around the failure time
B: Every log on the system, in full
C: The package manager history only
ANSWER: A
FEEDBACK: The service log normally records why it failed, which directs the fix. Reading everything fails on time, and package history helps only if an update is suspected.
[/CHECK]
[CHECK]
Q: Why change only one thing at a time when troubleshooting?
A: Because Linux allows only one change per session
B: Because you can then identify what fixed it and undo cleanly if it worsens
C: Because logs record only one change per day
ANSWER: B
FEEDBACK: Single changes make cause and effect clear and reversible. The other options are not real Linux limits.
[/CHECK]

KEY TAKEAWAYS
- Filesystem, permissions, and sudo are the base of Linux work
- Fix access by owner and group, never by opening it to everyone
- Package managers and systemd control software and services
- Logs usually record the fault before you need to guess
- Troubleshoot in order, one change at a time

GLOSSARY
Root directory — Top of the Linux filesystem, written as /
Permissions — Read, write, and execute rights for owner, group, and others
sudo — Runs one action with administrator rights, logged
Package manager — Installs and updates software from repositories
systemd — Starts and manages services on most Linux systems
Journal — The systemd log, read with journalctl

FURTHER READING
- CompTIA Linux+: https://www.comptia.org/certifications/linux
- Linux Foundation training: https://training.linuxfoundation.org/
- Kernel docs: https://www.kernel.org/doc/html/latest/

CERTIFICATION ALIGNMENT
Supports: CompTIA Linux+ (XK0-005) — system management, security, and troubleshooting domains; orientation toward Red Hat RHCSA, which is a hands-on exam.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
Readiness material is preparation guidance, not a guarantee of any exam result.
