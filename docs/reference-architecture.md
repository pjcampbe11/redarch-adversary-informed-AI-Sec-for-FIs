# AI Security Reference Architecture & Design Patterns

The "define and maintain AI security reference architectures, design patterns,
and standards" duty. This is the target-state architecture RedArch's controls
enforce, expressed as patterns an architect can hand to delivery teams.

---

## Principle: assume the model is compromised

The organising assumption is that **the LLM will, at some point, do what an
attacker tells it to** — via direct or indirect prompt injection. Security
therefore cannot live *inside* the model. It lives in the layers around it. Every
pattern below moves a control *out* of the prompt and *into* deterministic
infrastructure.

```
   user / channel
        │
        ▼
 ┌───────────────┐   input firewall: injection heuristics, PII pre-checks,
 │ INPUT GATEWAY │   rate limits, authN (Entra ID), request signing
 └──────┬────────┘
        ▼
 ┌───────────────┐   retrieval firewall: source allow-list, instruction
 │  RETRIEVAL    │   stripping, provenance/signing, PER-USER ENTITLEMENTS,
 │  (RAG)        │   PII tokenisation BEFORE the model sees it
 └──────┬────────┘
        ▼
 ┌───────────────┐   the model is UNTRUSTED. No secrets in the system prompt.
 │  LLM / AGENT  │   Tools are least-privilege, scoped, and cannot self-authorise.
 └──────┬────────┘
        ▼
 ┌───────────────┐   output firewall: DLP, safety classifier, schema validation,
 │ OUTPUT GATEWAY│   grounding/citation check
 └──────┬────────┘
        ▼
 ┌───────────────┐   action broker: HUMAN-IN-THE-LOOP + step-up auth for money
 │ ACTION BROKER │   movement; per-txn limits; full audit trail; enforced OUTSIDE
 │ (tools/APIs)  │   the model, in a service the model can only request from
 └───────────────┘
        │
        ▼  observability: log prompts, retrievals, tool calls, decisions →
           detection & response (the JD's "monitoring and logging for AI systems")
```

---

## Design patterns (and the control that enforces each)

| # | Pattern | Failure it prevents | Enforcing control |
|---|---|---|---|
| 1 | **Instruction/data separation** — user & retrieved text are data, never instructions | Prompt injection (LLM01) | input/retrieval firewall |
| 2 | **Retrieval entitlements** — row-level authZ applied at retrieval, per requesting user | Cross-customer PII disclosure (LLM02) | `CTRL-ENT-001` |
| 3 | **PII tokenisation before inference** — sensitive fields redacted/tokenised before the model | Data leakage via output | `CTRL-DLP-001` |
| 4 | **No secrets in prompts** — assume the system prompt is public | Secret/credential leak (LLM07) | `CTRL-SECRET-001` |
| 5 | **Least-privilege tools** — the model requests actions; a broker authorises them | Excessive agency (LLM06) | `CTRL-HITL-001` |
| 6 | **Human-in-the-loop for irreversible actions** — money movement needs approval + step-up auth | Injection → funds transfer | `CTRL-HITL-001` |
| 7 | **Source provenance** — retrieved/ingested content is signed and allow-listed | RAG poisoning (LLM04/08) | `CTRL-PROV-001` |
| 8 | **Rate limiting & cost caps** on exposed endpoints | Denial-of-wallet (LLM10) | `CTRL-RATE-001` |
| 9 | **Full AI observability** — prompts, retrievals, tool calls, decisions logged | Blind detection & response | (log standard) |

Patterns 2, 5, and 6 are the ones that turn a *breach of the model* into a
*non-event*. They are the highest-leverage architecture decisions for a
wealth-management copilot.

---

## Mapping to a Microsoft/Azure estate (Voya's shape)

Because Voya standardises on Azure (see
[voya-worked-example.md](voya-worked-example.md)), the patterns land on concrete
services:

| Pattern | Azure landing |
|---|---|
| Identity / authN | Microsoft **Entra ID**, conditional access, step-up (MFA) |
| Input/output firewall | Azure **AI Content Safety** + a custom prompt-shield gateway (APIM in front of Azure OpenAI) |
| Retrieval entitlements | Security trimming at the index (Azure AI Search / Databricks) — *not* in the prompt |
| Secrets | Azure **Key Vault**, managed identities — never in system prompts |
| Action broker | A dedicated service behind APIM; the agent gets scoped tokens, never direct transfer rights |
| Observability | Azure Monitor / Sentinel; log to the SOC's detection pipeline |
| Data provenance | Unity Catalog lineage on Databricks; signed ingestion |

---

## How controls-as-code fits

`policies/finserv-genai.yaml` is this reference architecture rendered as
*assertions*. A design review becomes: describe the proposed system in a spec
file, run `redarch controls`, and any pattern not implemented shows as a failing
control with its OWASP tag. That converts "architecture review" from a meeting
into a gate that can run in CI on every design change.
