Cloud Foundations

MODULE OVERVIEW
Level: Beginner | Time: 75 minutes | Prerequisites: Basic IT concepts.

LEARNING OBJECTIVES
After this module you can:
- Explain IaaS, PaaS, and SaaS with an example of each
- Apply the shared responsibility model to a service
- Name core compute, storage, and network services in Azure and AWS
- Describe cloud identity basics
- Compare pricing and support models

LESSON 1 — CLOUD MODELS AND SHARED RESPONSIBILITY
Cloud means computing delivered over the internet from a provider's data centers, paid for as you use it. The models describe how much the provider manages. IaaS: provider runs hardware and virtualization; you manage the operating system and applications — an Azure virtual machine or Amazon EC2. PaaS: provider also manages the operating system; you deploy your application — Azure App Service or AWS Elastic Beanstalk. SaaS: provider runs the whole application you use — Microsoft 365.

The shared responsibility model states who secures what, and it changes with the model. The provider always secures the buildings, hardware, and virtualization layer. You always own your data, accounts, and access decisions. On IaaS you patch the guest operating system; on PaaS the provider patches the platform and you secure your application; on SaaS you control user access and sharing. In an incident, this decides whether the fix is yours.

CASE BREAKDOWN: A firm moves its file server to an IaaS virtual machine and assumes the provider patches it. Months later the unpatched machine is compromised through a known flaw. The provider secured the host correctly; patching the guest was the firm's job. The model was the patching schedule they never wrote.

Worked examples — who does what:
1. SaaS email: provider runs it; you manage users, multi-factor authentication, and sharing.
2. IaaS server: provider secures the host; you patch, back up, and firewall it.
3. PaaS app: provider patches the platform; you secure code and accounts.
4. All models: your data and access decisions stay yours.

COMMON MISTAKE: Believing cloud means the provider handles security. What you put in it, and who can reach it, stays with you.

LESSON 2 — CORE SERVICES, IDENTITY, PRICING, AND SUPPORT
Core services fall into three groups in both clouds. Compute runs work: Azure Virtual Machines and Amazon EC2, plus app platforms. Storage holds data: Azure Blob Storage and Amazon S3, plus disks and databases. Networking connects it: Azure Virtual Network and Amazon VPC, with subnets and firewall rules deciding what reaches what. Names differ; jobs are the same.

Identity is the control point. Every person and service gets an identity, in Microsoft Entra ID for Azure and AWS IAM for AWS. Grant each only the access it needs, require multi-factor authentication, and review access when roles change. Most cloud incidents start with an identity that had too much access.

Pricing is pay-as-you-go by resource and time, with discounts for committing in advance. Costs grow quietly when test resources are left running, so tag resources, set budget alerts, and review monthly costs. Support is tiered: documentation at the base, then paid plans adding response times and a named contact.

CASE BREAKDOWN: A team spins up a large test server for a weekend project and forgets it. It runs for two months doing nothing. A budget alert would have flagged it in week one. The fix is process: tag resources with an owner and delete them on a date written down at creation.

Checklist — starting a cloud resource:
- Name the owner and tag the resource.
- Grant the least identity access needed.
- Set a budget alert before it runs.
- Write the review or deletion date down.

COMMON MISTAKE: Treating the first bill as the cost lesson. Set budgets and alerts on day one; a bill reports money already spent.

HANDS-ON EXERCISE
Scenario: On paper, a small firm chooses services for email, one business application, and file storage.
Decision point 1: Email. Correct path: Choose SaaS. The provider runs it; the firm keeps user access, multi-factor authentication, and sharing settings.
Decision point 2: The application vendor requires full control of the operating system. Correct path: Choose IaaS, and record that the firm owns patching, backup, and firewall rules.
Decision point 3: A test server is proposed with no owner or end date. Correct path: Do not approve it until it has an owner tag, a budget alert, and a deletion date.

KNOWLEDGE CHECK
[CHECK]
Q: Under IaaS, who patches the guest operating system on a virtual machine?
A: The cloud provider, in all models
B: You, the customer
C: The software vendor who sold the application
ANSWER: B
FEEDBACK: IaaS gives you the machine, so its operating system is yours to patch. The provider-patches-all option fails because that duty moves to the provider only toward PaaS and SaaS.
[/CHECK]
[CHECK]
Q: A firm uses SaaS email. Which duty stays with the firm?
A: Patching the provider's mail servers
B: Physical security of the data center
C: Cooling the provider's hardware
D: Managing user access, multi-factor authentication, and sharing settings
ANSWER: D
FEEDBACK: In every model your data, accounts, and access decisions stay yours. The other options are provider facilities duties, never transferred to a SaaS customer.
[/CHECK]
[CHECK]
Q: What prevents a forgotten test server from billing quietly for months?
A: Owner tags, a budget alert, and a written deletion date
B: Choosing a larger server size
C: Paying the bill annually
ANSWER: A
FEEDBACK: Tags assign ownership, alerts surface spend early, and a deletion date ends the resource. A larger server only raises the cost.
[/CHECK]

KEY TAKEAWAYS
- The three models describe how much the provider manages
- Shared responsibility always leaves data and access with you
- Compute, storage, and networking jobs match in Azure and AWS
- Identity, with least access and a second factor, is the control point
- Tags, budgets, and deletion dates control costs

GLOSSARY
IaaS — Provider hardware, your operating system
PaaS — Provider platform, your application
SaaS — Provider runs the application you use
Shared responsibility — Split of security duties between provider and customer
Virtual network — Your private network inside a cloud provider
Tag — Label naming a resource's owner or project

FURTHER READING
- Microsoft AZ-900: https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/
- AWS Cloud Practitioner: https://aws.amazon.com/certification/certified-cloud-practitioner/

CERTIFICATION ALIGNMENT
Supports: Microsoft AZ-900 — cloud concepts, architecture and services, management and governance; AWS Certified Cloud Practitioner (CLF-C02) — cloud concepts, architecture and services, management and governance.
Alignment means this module teaches the knowledge these certifications test in this area. Completing it does not by itself earn any certification — vendor exams are taken separately through the certification body.
