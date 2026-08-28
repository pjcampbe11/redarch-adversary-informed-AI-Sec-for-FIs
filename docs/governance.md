# AI Security Governance Framework

The "AI security governance frameworks, guardrails, and risk management" and
"compliance, privacy, and responsible AI" duties. This describes the operating
model around the technical controls — who decides, what's required, and how it's
evidenced.

---

## Operating model

Three bodies, one gate:

- **AI Security Standards** (the *what*) — a versioned baseline of required
  controls, expressed as code in `policies/`. Changing the baseline is a
  reviewed pull request, not a wiki edit.
- **AI Review Board** (the *decision*) — cross-functional (security, data
  science, platform, legal/privacy, compliance). Approves new AI use cases
  against their risk tier.
- **AI Red Team** (the *evidence*) — independently tries to break approved
  systems; feeds findings back into the standards. This is the offensive
  function the JD's "enhance security posture" duty asks you to build.

The single gate: **no AI system reaches production with an open critical finding
or a failing critical control.** RedArch makes that gate executable
(`redarch assess --fail-on-finding --fail-on-violation`).

---

## Risk tiering

Not every AI system needs the same rigor. Tier by *data* and *agency*:

| Tier | Definition | Example | Required |
|---|---|---|---|
| **T3 Critical** | Touches participant PII/financial **and** can take state-changing actions | Advisor copilot with `transfer_funds` | Full threat model + all critical controls + red-team sign-off + HITL |
| **T2 Elevated** | Touches sensitive data **or** has agency, not both | RAG Q&A over participant docs (read-only) | Threat model + entitlement/DLP controls + red-team |
| **T1 Standard** | No sensitive data, no agency | Internal doc summariser on public content | Baseline controls + spot check |

The Voya worked-example copilot is **T3** — the highest tier, which is why it is
the priority target in [prioritization.md](prioritization.md).

---

## NIST AI RMF alignment

The governance model maps cleanly onto the four NIST AI RMF functions, which is
the language regulators and auditors increasingly expect:

| Function | What it means here | RedArch artifact |
|---|---|---|
| **Govern** | Policies, roles, risk tiers, accountability | `policies/*.yaml`, this document |
| **Map** | Enumerate context, data flows, and threats per system | `threatmodel/` output |
| **Measure** | Empirically test controls; quantify residual risk | `redteam/` findings + posture grade |
| **Manage** | Prioritise, assign, and track remediation | tagged JSON reports → ticketing |

---

## Compliance & privacy hooks

- **Auditability** — `redarch ... --json` emits machine-readable control and
  finding records suitable as audit evidence and control-assessment artifacts.
- **Privacy by design** — the reference architecture requires PII tokenisation
  *before* the model and entitlements *at retrieval*; both are enforced as
  controls (`CTRL-DLP-001`, `CTRL-ENT-001`), so a privacy review has objective
  pass/fail evidence.
- **Responsible AI** — security, privacy, and risk are integrated into the same
  spec-driven review rather than bolted on, which is what "integrating
  security, privacy, and risk considerations into enterprise AI standards" asks
  for.
- **Regulatory context** — for a US retirement/wealth firm, expect SEC/FINRA
  suitability and recordkeeping expectations, state privacy law, and
  model-governance scrutiny. The control baseline is the place to encode
  firm-specific obligations as they're confirmed with legal.

---

## Third-party & generative-AI usage governance

The JD calls out "secure use of generative AI, LLMs, and third-party AI services
through policy, technical controls, and architectural review." Practically:

- An **allow-list** of approved models/endpoints (e.g. specific Azure OpenAI
  deployments), enforced at the gateway, not by policy PDF.
- **Data-egress rules** — what participant data may leave the tenancy for which
  model; enforced by the retrieval/output firewalls.
- **Vendor assessment** — every third-party AI service gets a threat model and a
  tier before use; the spec/controls flow applies to vendor systems too.
