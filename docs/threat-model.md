# AI Threat Modeling Methodology

How RedArch turns a system description into a threat model, and the framework
mappings behind it. This is the "Threat Modeling & Risk Management" duty made
mechanical and repeatable.

---

## The method

Classic STRIDE and app threat modeling don't capture how LLM systems fail — the
attack surface is the *content*, the *retrieval*, and the *agency*, not just the
network and the code. RedArch models three things per component:

1. **What data it touches** (`pii`, `financial`, `phi`, `confidential`).
2. **What it can do** (its `tools` — especially state-changing ones).
3. **Where untrusted input reaches it** (`internet_exposed`, `untrusted_input`,
   and any `rag`/`agent` retrieval).

From those three, threats fall out deterministically via a transparent rule
table (`redarch/threatmodel/generate.py`). Transparency is the point: an
architect can audit *why* each threat was raised, unlike a black-box scorer.

Run it:

```bash
redarch threatmodel --spec examples/voya_wealth_advisor.yaml
```

On the Voya worked example this generates **16 threats** across the copilot, the
RAG index, the Azure OpenAI endpoint, and the Databricks pipeline.

---

## The threat classes RedArch reasons about

| Threat class | Trigger in the spec | OWASP LLM | MITRE ATLAS | Why it matters for wealth mgmt |
|---|---|---|---|---|
| Direct prompt injection | any llm_app/agent/rag | LLM01 | AML.T0051.000 | Overrides policy; entry point for everything else |
| **Indirect prompt injection** | rag/agent (retrieval) | LLM01, LLM08 | AML.T0051.001 | **Highest-signal risk** — a poisoned doc/CRM note runs as instructions |
| RAG / data-store poisoning | rag/agent | LLM04, LLM08 | AML.T0070 | Adversary biases or hijacks future answers |
| **Excessive agency** | component has `tools` | LLM06 | AML.T0053 | A successful injection reaching `transfer_funds` = direct loss |
| **Sensitive data disclosure** | data ∋ pii/financial | LLM02 | AML.T0057 | Broken row-level authZ at retrieval → participant PII leak |
| System prompt / config leakage | untrusted_input | LLM07 | AML.T0057 | Secrets in prompts become recoverable |
| Unbounded consumption | internet_exposed | LLM10 | — | Denial-of-wallet / quota exhaustion |
| Model theft / extraction | model_endpoint/training | LLM10 | AML.T0024 | Lower priority on managed Azure OpenAI |
| Training-data poisoning | training/data_pipeline | LLM04 | AML.T0020 | Backdoors planted upstream in the lakehouse |

Bold rows are the ones prioritised for a financial advisor copilot — see
[prioritization.md](prioritization.md) for the reasoning.

---

## Framework alignment

RedArch is deliberately a thin, opinionated layer over public frameworks so its
output plugs into an existing risk process.

### OWASP Top 10 for LLM Applications (2025)

Every finding, threat, and control carries `LLMxx` tags. The suite covers:
`LLM01` prompt injection, `LLM02` sensitive information disclosure, `LLM04` data
& model poisoning, `LLM06` excessive agency, `LLM07` system-prompt leakage,
`LLM08` vector/embedding weaknesses, `LLM10` unbounded consumption.

### MITRE ATLAS

Probes and threats map to ATLAS techniques (`AML.Txxxx`) so offensive activity is
described in the same adversarial-ML language a detection team already tracks —
directly serving the JD's "partner with detection and response" duty.

### NIST AI RMF (Govern / Map / Measure / Manage)

| RMF function | RedArch surface |
|---|---|
| **Govern** | `policies/` — controls-as-code encode the governance baseline |
| **Map** | `threatmodel/` — enumerate context, data, and threats |
| **Measure** | `redteam/` — empirically test whether controls hold; posture grade |
| **Manage** | `report/` — prioritised, tagged findings routed to owners |

See [governance.md](governance.md) for the full RMF write-up.

---

## Extending the threat model

The rule table is intentionally simple to edit. To add a threat class, add a
predicate + `_t(...)` template in `generate.py`; it will automatically appear in
reports and inherit the OWASP/ATLAS tagging convention. Because the threat model
and the controls policy share the same spec, a new threat should always be paired
with a new control assertion that would detect it.
