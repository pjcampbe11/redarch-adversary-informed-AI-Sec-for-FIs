# Modules — every file, described

The Azure code from *Breaking the Advisor Copilot*, broken out one concern per
file. Each entry: what it is, the field-guide chapter it came from, and how it
connects to the rest.

## Configuration
- **`azure_advisor/config.py`** — one typed settings object for every endpoint,
  deployment name, and policy knob, sourced from environment variables. No
  secrets — only names and policy. *Everything imports `SETTINGS` from here.*

## `identity/` — the spine (Ch. 09, 14)
- **`credentials.py`** — password-less **service** auth. `DefaultAzureCredential`
  (managed identity) + a bearer-token provider for Azure OpenAI. No API keys.
- **`obo.py`** — **on-behalf-of** token exchange (MSAL). Makes the backend act as
  the *user*, so downstream authorization uses the user's permissions. The fix
  for the confused deputy. *Feeds the caller's groups/scopes into the pipeline.*

## `aoai/` — Azure OpenAI (Ch. 04, 11)
- **`client.py`** — keyless chat client with tool-calling. Normalizes the SDK
  response so the app doesn't depend on api-version drift. Surfaces tool calls;
  never executes them.
- **`target.py`** — the same endpoint wrapped as a **red-team target** for the
  harness, plus `classify_platform_block()` to keep Azure content-filter blocks
  from being miscounted as model refusals.

## `safety/` — the firewall (Ch. 05, 06, 07)
- **`content_safety.py`** — Azure AI Content Safety. `shield_input()` runs Prompt
  Shields on the prompt **and** the retrieved documents (direct + indirect
  injection). `moderate_output()` screens the answer. `dlp_scan()` is a
  deterministic SSN/account sweep that runs even during a safety outage. Fails
  closed.

## `rag/` — retrieval over participant data (Ch. 07, 13)
- **`retrieval.py`** — **security-trimmed** Azure AI Search. The entitlement lives
  in the query filter (built from the caller's Entra groups), applied to lexical
  and vector paths. The crown-jewel data control.
- **`redaction.py`** — masks PII to last-4 before the model sees it.
- **`grounding.py`** — assembles the grounded prompt, **spotlighting** retrieved
  text as `<doc>` data (not instructions). Holds the system prompt — which
  contains no secrets, by design.

## `agent/` — tools and the broker (Ch. 08, 12)
- **`tools.py`** — tool schemas the model may request, split into read vs. write
  trust tiers.
- **`broker.py`** — authorizes tool calls **out of band**: read-tier executes if
  in scope; write-tier (money) applies policy → human-in-the-loop + step-up for
  external/high-value. The excessive-agency control.

## Orchestration
- **`pipeline.py`** — ★ **the orchestrator.** Wires all of the above in order for a
  single request, fail-closed at each gate. Ships with a production wiring
  (`build_production_pipeline`) and an in-memory `--demo`. *Read this first.*

## `redteam/` — offensive testing (Ch. 03, 04)
- **`campaign.py`** — wired to the **real** `xteaming` harness
  (`pjcampbe11/multi-agent-harness`). `AzureOpenAILLMClient` adapts our keyless
  `AoaiClient` to the harness's `LLMClient.chat` interface, so the
  Planner/Attacker/Verifier/Optimizer loop attacks the real Azure deployment.
  Builds `Orchestrator(authorized=True)`, enforces verifier≠target, loads
  objectives from JSONL, and labels Azure content-filter blocks as `platform_block`
  (not model refusals). Install the harness or set `XTEAMING_PATH`; run
  `python -m azure_advisor.redteam.campaign --authorized`. Example objectives:
  `examples/advisor_scope.jsonl`.

## `infra/` — the estate (Ch. 11, 14, 15)
- **`provision.sh`** — Azure CLI: create AOAI + Search + Content Safety with
  **public access disabled** and grant the app **least-privilege** data-plane roles.
- **`main.bicep`** — the same estate as declarative IaC (keyless, private,
  least-privilege).

## Config templates
- **`.env.example`** — copy to `.env`, fill endpoints/ids.
- **`requirements.txt`** — the Azure SDKs (only needed to run against real Azure;
  the demo needs none of them).
