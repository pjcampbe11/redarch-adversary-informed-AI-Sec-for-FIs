# Architecture — How the Moving Pieces Work Together

This is the guided tour of the Azure code. Read it once and `pipeline.py` will
read like prose. The system is a wealth-management **Advisor Copilot**, and its
single design commitment is:

> **The model is untrusted.** Every control lives in the layers *around* it.
> Injection can beat the model — the surrounding layers make that not matter.

---

## The one-screen picture

```
   user + their Entra token
            │
            ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │                         AdvisorPipeline.handle()                      │
 │                                                                       │
 │  1 identity/obo        act AS THE USER (not the service) ── confused  │
 │     │                                                     deputy fix  │
 │     ▼                                                                 │
 │  2 rag/retrieval       search FILTERED by the user's Entra groups     │
 │     ▼                  (entitlement lives in the query, not the prompt)│
 │  3 rag/redaction       mask PII to last-4 before the model sees it    │
 │     ▼                                                                 │
 │  4 safety/shield_input Prompt Shields: direct + INDIRECT injection    │
 │     ▼                  (scans the retrieved docs too)                 │
 │  5 aoai/client ─────────▶  THE MODEL (untrusted). May only REQUEST    │
 │     ▼                      tools; holds no capability.                │
 │  6/7 safety/moderate    moderation + deterministic DLP on the answer  │
 │     ▼                                                                 │
 │  8 agent/broker        authorize tool calls OUT OF BAND:              │
 │                        HITL + step-up + least-privilege scopes        │
 └─────────────────────────────────────────────────────────────────────┘
            │
            ▼
   answer  +  (approved) actions

  everything above runs on Azure with managed identity (no keys) and private
  networking (infra/): the estate is never internet-reachable.
```

Each numbered step is exactly one module. The model is step 5, in the middle,
bracketed by controls on both sides.

---

## The request trace, step by step

Follow a single call through `AdvisorPipeline.handle(user_token, user_query)`:

**1. Identity — `identity/obo.py`.**
The copilot received the user's access token. Before doing anything, it exchanges
that token **on-behalf-of** the user for a downstream token scoped to the RAG API.
From here on, the request acts *as the user*, with the user's permissions — not as
the all-powerful service identity. This is the fix for the **confused deputy**: the
data layer will enforce the user's entitlements because the calls arrive as the
user. The caller's Entra **group ids** (for step 2) and **scopes** (for step 8)
come from the validated token claims.

**2. Retrieve — `rag/retrieval.py`.**
Azure AI Search is queried with a **security-trimming filter** built from the
caller's group ids. Only rows whose ACL intersects the caller's groups are ever
returned. The same filter is applied to the vector path, closing the embedding
leak. The model can *ask* for another customer's record; the row is simply never
retrieved.

**3. Redact — `rag/redaction.py`.**
Retrieved chunks are passed through PII masking (SSN → `***-**-4417`, long numbers
→ last-4) *before* the model or the shield sees them. Even entitled data is
minimized, so a leak or a log line exposes nothing usable.

**4. Input firewall — `safety/content_safety.py::shield_input`.**
Azure AI Content Safety **Prompt Shields** scans the user prompt (direct jailbreak)
**and every retrieved document** (indirect injection). If either trips, the request
is blocked here — the model is never called. This is the deterministic half of the
indirect-injection defense; the in-prompt half (spotlighting) is in step 5.

**5. Model — `aoai/client.py`.**
The grounded messages (`rag/grounding.py` wraps documents in `<doc>` tags and tells
the model they are data, never instructions) go to the Azure OpenAI deployment via
the **keyless** client. The model answers and may **request** tool calls. It cannot
execute anything — it holds no capability.

**6/7. Output firewall — `safety/content_safety.py`.**
The answer runs through content **moderation** and a deterministic **DLP** sweep. If
a sensitive identifier (SSN, account number) somehow appears, the response is
withheld rather than leaked — a last line behind the retrieval-time entitlement.

**8. Broker — `agent/broker.py`.**
Any tool call the model requested is authorized **out of band**. Read-tier calls
(`get_balance`) execute if the caller holds the scope. Write-tier calls
(`transfer_funds`) apply money-movement **policy**: external or high-value transfers
return `NEEDS_APPROVAL` (human-in-the-loop + step-up auth); the broker never lets the
model move money on its own. A poisoned document that made the model emit
`transfer_funds` lands here and stops.

**Fail closed everywhere.** OBO failure → no token, no data. Content-Safety outage →
treat as unsafe and block. No caller groups → the search filter matches nothing.

---

## Why this order

The sequence is not arbitrary — each step depends on the one before:

| Step | Depends on | Because |
|---|---|---|
| retrieve (2) | identity (1) | the entitlement filter needs the *user's* groups |
| redact (3) | retrieve (2) | you can only redact what you retrieved |
| shield (4) | retrieve (3) | indirect injection hides *in the retrieved docs* |
| model (5) | 1–4 | the model must only see entitled, redacted, shielded input |
| broker (8) | identity (1) | authorization uses the *caller's* scopes, not the model's text |

---

## Trust boundaries

```
 UNTRUSTED                 SEMI-TRUSTED                    TRUSTED (enforced)
 ─────────                 ────────────                    ──────────────────
 user prompt               the model (aoai)                identity / OBO
 uploaded docs             its text output                 entitlement filter
 tool ARGUMENTS  ────────▶ its tool REQUESTS   ──────────▶ the broker's decision
 retrieved content                                         infra RBAC + network
```

Everything the model touches is untrusted or semi-trusted. Everything that
actually grants data or moves money is on the trusted side and is enforced by
Azure primitives (Entra, Search filters, RBAC, private endpoints), not by the
model's cooperation.

---

## Threat → control map (which file stops what)

| Crown jewel (field guide) | Stopped by | File |
|---|---|---|
| Tool-abuse → funds (Ch.08) | HITL + least-privilege broker | `agent/broker.py` |
| RAG cross-customer exfil (Ch.07) | security-trimmed retrieval + DLP | `rag/retrieval.py`, `safety/` |
| Indirect injection (Ch.06) | Prompt Shields + spotlighting | `safety/`, `rag/grounding.py` |
| Direct injection / leak (Ch.05) | shields + no secrets in prompt | `safety/`, `rag/grounding.py` |
| Identity bypass (Ch.09/14) | OBO + least-privilege RBAC | `identity/`, `infra/` |
| Exfil / DoW (Ch.10/15) | private endpoints + quotas | `infra/` |

---

## Running it

```bash
pip install -r requirements.txt
python -m azure_advisor.pipeline --demo     # in-memory, no Azure needed
```

The demo runs four requests through the *same* pipeline and prints the trace so
you can watch which control fires: a benign entitled query (answers), an
un-entitled cross-customer pull (retrieves nothing), a poisoned document (blocked
at the input firewall), and a transfer attempt (routed to the broker for
approval). For real Azure, fill `.env` (see `.env.example`), run
`infra/provision.sh`, and use `build_production_pipeline()`.
