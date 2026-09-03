# Skills Breakdown — AI Security Architect 

Every skill, qualification, and differentiator called out in the posting, with a
plain description of what it means *for this role* and, where relevant, how the
RedArch framework demonstrates it. Grouped as the posting groups them.

---

## Core qualifications (Knowledge & Experience)

**Bachelor's (Master's preferred) in CS / IS / business, or equivalent.**
Baseline credential; the "or equivalent + extensive project experience" clause
means a strong portfolio (like this repo) can substitute for a specific degree.

**7+ years as an architect, 3+ in AI and generative AI.**
They want someone who has *shipped* architecture, not just advised — and who has
hands-on GenAI depth (LLMs, RAG, agents), not just classical ML. Translation:
you can stand in front of an Azure OpenAI/agent design and say what breaks.

**5+ years IT/business experience owning strategy, analytics, program
management, app dev, middleware, DB, or operations.**
Breadth requirement: the architect has to speak to the whole stack the AI sits
on, not just the model. In a wealth build-out that's identity, data pipelines,
APIs, and the retirement platform.

---

## Duty areas (what you'll actually own)

**AI security architecture & governance.** Define and maintain AI security
*reference architectures, design patterns, and standards* across the full
lifecycle — ingestion, training, deployment, inference, monitoring — and stand up
governance frameworks and guardrails aligned to enterprise security and
compliance. → RedArch `controls/` + `docs/reference-architecture.md`,
`docs/governance.md`.

**Enhance security posture (AI *for* security).** Drive the security team to
*use* AI/ML — including agentic AI — to improve detection and cloud-ops. This is
the offensive-defensive flip: not just securing AI, but weaponising it for the
defenders. → `redteam/` harness as a CI gate; the roadmap in
`docs/prioritization.md`.

**Threat modeling & risk management.** Run AI-specific threat modeling and risk
assessments covering data poisoning, adversarial attacks, model theft, prompt
injection, and unauthorised model usage; define mitigations across cloud, app,
API, and data layers; partner with detection & response on monitoring/logging.
→ `threatmodel/` generator + `docs/threat-model.md`.

**Secure design & implementation.** Review and approve AI solution designs;
design controls for secure data pipelines, model storage, controlled model
access, and protected inference endpoints; guide dev teams on secure coding, API
security, IAM, and secrets management for AI workloads. → `controls/`
policy-as-code makes "design review" a repeatable, testable gate.

**Compliance, privacy & responsible AI.** Work with legal/privacy/compliance so
AI meets regulatory and internal obligations; support audits and control
assessments; integrate security/privacy/risk into enterprise AI standards. →
JSON control reports are audit artifacts; NIST AI RMF mapping in
`docs/governance.md`.

**Collaboration & leadership.** Be the AI-security SME across the org; *translate
complex AI risk into executive-level guidance*; mentor engineers/architects.
This is weighted heavily — the posting is as much about influence as tech. → the
posture grade + exposure score exist to make findings executive-legible.

---

## Differentiators (the long list, each written up)

The posting lists many "expert level" differentiators. Most are
consulting/enterprise-architecture competencies, not AI-specific — a signal that
Voya wants an architect who can operate at the business/EA level, with AI
security as the specialty. Descriptions below.

- **Strategic planning / leadership / business relationship & process
  management.** Set multi-year AI-security direction, own senior stakeholder
  relationships, and shape the *processes* AI plugs into — not just point tools.
- **Business & operating models (existing, new, emerging, hybrid).** Understand
  how the firm actually makes money so security enables rather than blocks new AI
  revenue (e.g. a wealth-management copilot).
- **Applying existing/new/emerging technology to new business designs.** Keep up
  with the frontier (agentic AI, new model classes) and translate it into
  designs the business can adopt safely.
- **Business transformation & process redesign.** AI programs are transformation
  programs; you'll redesign workflows, not bolt AI onto old ones ("process before
  AI").
- **Designing business processes, functions & org structures.** Able to define
  *how the work and the teams* are arranged around AI — e.g. an AI review board,
  a red-team function.
- **Facilitation & organizational change management.** Drive adoption of new
  security standards across resistant teams; run workshops, not just write docs.
- **Analytical & conceptual skills — original concepts and theories.** Invent
  frameworks where none exist (AI threat modeling is still being invented — this
  repo is an example of exactly that).
- **Leading multi-disciplinary, high-performance teams.** Pull together security,
  data science, platform, legal into one delivery.
- **Program management across multiple related projects.** Coordinate resources
  and goals across a portfolio of AI initiatives.
- **Developing/monitoring efficient, effective solutions to complex problems.**
  Own outcomes end to end, including measuring whether controls actually work
  (RedArch's whole thesis).
- **Finance, accounting, valuation & metrics development.** Speak the language of
  a financial-services firm; quantify risk in business terms.
- **Statistical & information analysis (a plus).** Read model behavior and data
  quantitatively — useful for poisoning/adversarial detection.
- **Communicate, influence, persuade — with business & IT leaders and peers.**
  The single most repeated theme; the role lives or dies on executive
  translation.
- **"Use the language of business leaders / join the conversation."** Frame AI
  risk as business risk (fraud loss, regulatory exposure, customer trust), not
  CVEs.
- **Adapt to rapidly changing technology and apply it to business needs.**
  Frontier-tracking as a core competency, not a hobby.
- **Establish & maintain business-partner trust and confidence.** Be the person
  the business *wants* to bring AI ideas to early.
- **Analyze project needs, determine resources, solve elusive multi-environment
  problems.** Debug risks that span cloud + app + data + identity — the
  cross-layer nature of AI attacks.
- **Business process management, workflow & integration methods/tools.**
  Understand how AI integrates with existing systems (APIs, middleware, the
  retirement platform).
- **Team player, facilitator, respected/trusted leader.** Soft-skill weighting.
- **Technology- and vendor-neutral; results over preferences.** Notable given the
  Azure-heavy estate — they want judgement, not evangelism.
- **Intellectual curiosity & integrity; motivated by long-term outcomes.**
  Culture-fit signals.
