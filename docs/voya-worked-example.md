# Worked Example: Voya Financial

This document is the "know the target" layer. It summarises what Voya does, why
the AI Security Architect role exists now, and — as best as can be established
from public sources — who their AI vendors are. Everything downstream (threat
model, controls, priorities) is scoped to this picture.

> Sources are listed at the bottom. Vendor attributions are drawn from public
> reporting and Voya's own material; treat anything not on a Voya-owned page as
> "reported, verify in interview."

---

## What Voya does

Voya Financial (NYSE: **VOYA**) is a US retirement, investment, and benefits
company — the former US retirement arm of ING, spun out and rebranded in 2014.
It runs three businesses that matter for AI risk:

1. **Workplace Solutions / Retirement** — the core. Voya administers
   employer-sponsored retirement plans (401(k), 403(b), 457) and, after the
   **OneAmerica** acquisition (announced Sept 2024, closed Jan 2025, ~**$60B**
   in retirement plan assets), now serves **~8 million participants**. This is a
   vast store of participant PII and financial data — exactly the data a
   "wealth-management offering" and an advisor copilot would sit on top of.
2. **Voya Investment Management (Voya IM)** — asset management. Notably runs a
   **"Machine Intelligence"** family of AI/ML-driven equity strategies (a decade+
   of ML-in-investing experience by their own account).
3. **Health / Benefits** — stop-loss and workplace benefits (adds PHI-adjacent
   data to the risk surface).

**Why the role, now:** Voya is moving from ML-for-investing toward
customer-facing and operational **generative AI**. An August 2026 Forbes profile
framed their approach as "**process before AI**" — redesigning the customer
experience first, then applying AI — which is precisely the environment where an
AI Security Architect is hired to put guardrails around a build-out that is
already in motion. The wealth-management angle means the highest-value AI targets
sit directly on participant money and PII.

---

## Voya's AI / data stack (reported)

| Layer | Vendor / technology | Confidence | Notes |
|---|---|---|---|
| Cloud + data science platform | **Microsoft Azure** | High | Publicly reported as deploying Azure to boost data-science capabilities |
| ML / data engineering | **Azure Databricks** (Databricks on Azure) | High | Named in reporting on Voya's ML in finance |
| Generative AI / assistants | **Azure OpenAI Service** / **Microsoft Copilot** ecosystem | Medium | Inferred from Azure standardisation + 2026 CX-AI initiative; confirm exact deployments |
| Proprietary investing ML | **Voya IM "Machine Intelligence"** | High | In-house ML equity strategies; vendor/frameworks not disclosed |
| Data infrastructure | Azure data services (Fabric/Synapse-class), Databricks Lakehouse | Medium | Consistent with an Azure+Databricks estate |

**Architectural read for a red-teamer:** a Microsoft-centric estate. That means
the realistic GenAI attack surface is **Azure OpenAI deployments, Copilot /
Copilot Studio agents, and RAG over Databricks/Azure-hosted participant data**,
governed by **Entra ID** identity and Azure networking. Model theft and
weight-exfil are lower priority (managed models); **prompt injection, RAG data
governance, agent tool-abuse, and identity/entitlement bypass are the crown
jewels.** RedArch's default probe suite and `finserv-genai` policy are tuned to
exactly that shape — see [prioritization.md](prioritization.md).

The RedArch example spec (`examples/voya_wealth_advisor.yaml`) encodes this: an
`agent` advisor-copilot with a `transfer_funds` tool over a `rag`
participant-index, an `azure-openai` model endpoint, and a `databricks`
feature pipeline.

---

## The role in one line

Own the security architecture, threat models, guardrails, and governance for
Voya's AI/GenAI — especially the wealth/retirement copilots that touch ~8M
participants' money — and translate that risk to executives. RedArch is a
reference implementation of the *technical* half of that job.

---

## Sources

- [Voya Financial company overview — Forbes](https://www.forbes.com/companies/voya-financial/)
- [Voya IM firm overview (Q1 2026, PDF)](https://individuals.voya.com/document/firm-profile/voya-im-firm-overview.pdf)
- [Voya puts process before AI to rethink customer experience — Forbes, Aug 19 2026](https://www.forbes.com/sites/stevennorton/2026/08/19/voya-puts-process-before-ai-to-rethink-customer-experience/)
- [Voya deploying Microsoft Azure to boost data science — FIMA/WBR](https://fimaus.wbresearch.com/blog/voya-financial-deploying-microsoft-azure-boost-data-science-capabilities-strategy)
- [Machine Learning in Finance: Voya, SWIFT, Icatu leverage Azure Databricks — ITMAGINATION](https://www.itmagination.com/blog/revolutionizing-finance-voya-swift-icatu-seguros-leverage-azure-databricks-ai-machine-learning)
- [Voya IM — Machine Intelligence: the third wave of investing](https://institutional.voya.com/machine-intelligence-welcome-third-wave-investing)
- [Voya to acquire OneAmerica's retirement plan business — Voya.com](https://www.voya.com/news/2024/09/voya-financial-to-acquire-oneamerica-financials-retirement-plan-business)
- [Voya completes OneAmerica acquisition — now ~8M participants — Voya.com](https://www.voya.com/news/2025/01/voya-financial-completes-acquisition-oneamerica-financials-retirement-plan-business)
