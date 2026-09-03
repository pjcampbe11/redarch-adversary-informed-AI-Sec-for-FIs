## General financial-institution worked example

*Security Architecture*

Every threat model, priority order, and control baseline in this guide needs a target to be scoped against. This chapter is a template for building that target profile from public information for *any* large financial institution — illustrated with a composite, representative profile rather than any single named organization.

### The archetype

A large retirement, wealth, or banking institution standing up GenAI on top of an existing regulated data estate typically looks like this: a core administration/record-keeping business serving millions of customers (often grown through acquisition, which matters because it means data from multiple legacy systems is being consolidated into one estate); a proprietary quantitative or investment-management function with in-house ML that predates the current GenAI wave; and an adjacent line of business (health, benefits, insurance) that adds PHI-adjacent data to the risk surface. The GenAI layer — an "advisor copilot," a claims assistant, an internal ops copilot — gets built on top of all of it, which is exactly why the crown jewels in Ch. 01 are money movement and customer PII rather than model novelty.

### A representative large-FI AI/data stack

This is the technology-stack profile this entire guide is built around and tuned against. It reflects the shape most large, Microsoft-centric financial institutions land on — confirm the specifics for any real target in discovery rather than assuming them.

| Layer | Technology | Typical confidence | Notes |
|---|---|---|---|
| Cloud + data science platform | **Microsoft Azure** | High | The default for large regulated FIs standardizing on Microsoft |
| ML / data engineering | **Azure Databricks** | High | Common pairing for lakehouse + feature pipelines on Azure |
| Generative AI / assistants | **Azure OpenAI Service** / **Microsoft Copilot** ecosystem | Medium | Inferred from Azure standardization plus a customer-experience AI initiative; always confirm exact deployments |
| Proprietary decisioning ML | In-house ML/quant models | High | Frameworks and vendors typically undisclosed publicly |
| Data infrastructure | Azure data services (Fabric/Synapse-class), Databricks Lakehouse | Medium | Consistent with an Azure+Databricks estate |

> **Architectural read for a red-teamer**
>
> A Microsoft-centric estate means the realistic GenAI attack surface is **Azure OpenAI deployments, Copilot / Copilot Studio agents, MCP-server-backed tools, and RAG over Databricks/Azure-hosted customer data**, governed by **Entra ID** identity and Azure networking. Model theft and weight-exfil stay lower priority (managed models); prompt injection, RAG data governance, agent tool-abuse, and identity/entitlement bypass are the crown jewels. RedArch's default probe suite and `finserv-genai` policy are tuned to exactly this shape.

### Building this profile for a real organization

The method is the same regardless of which institution you're scoping:

1. **Start from what the firm says about itself** — investor materials, engineering blog posts, conference talks, job postings for AI/platform roles (a posting for "Azure OpenAI," "Copilot Studio," or "Databricks" experience is a strong signal of the actual stack).
2. **Corroborate with independent reporting** — trade press on cloud/AI vendor deployments, case studies published by the cloud vendor itself, analyst coverage of the firm's technology strategy.
3. **Rate your confidence per layer** — "high" for anything on the firm's own properties or the vendor's named case studies, "medium" for reporting that infers rather than states, "low" for anything you're extrapolating from industry norms alone. Carry that confidence rating into the threat model so downstream reviewers know what's confirmed versus assumed.
4. **Scope the blast radius from the business, not the tech** — how many customers, what data classes (PII, financial, PHI), what M&A history (consolidated legacy data stores are a common source of inconsistent entitlements), and what state-changing actions a copilot could plausibly be wired to.

> **Explain it like I'm the intern — why build a profile instead of just picking a generic target?**
>
> A threat model scoped to "some company, somewhere" produces generic findings nobody can prioritize. A threat model scoped to "this firm, ~N million customers, this specific acquisition history, this specific cloud commitment" produces findings with a real blast radius attached — which is what gets a fix funded. The profile isn't paperwork; it's the input the whole rest of the pipeline depends on.

### Other considerations across comparable large FIs

When you repeat this exercise across a handful of peer institutions — useful when benchmarking a program or preparing a cross-industry threat model — a few additional considerations tend to recur beyond the core stack table above:

- **Regulatory regime overlap** — a firm that spans retirement, wealth, and insurance often answers to multiple regulators (SEC/FINRA suitability rules, state insurance commissioners, state privacy law) simultaneously; the control baseline should trace to all of them, not just the most obvious one.
- **M&A-driven data consolidation** — acquired books of business frequently arrive with their own legacy entitlement models; a RAG index built by merging two customer stores is a common place for Ch. 07's embedding-leak gotcha to appear silently.
- **In-house quant/ML teams predating the GenAI build-out** — these teams often have their own model-risk-management process (SR 11-7-style validation) that the new GenAI governance program needs to integrate with rather than duplicate.
- **Customer-experience-first AI framing** — firms that publicly frame AI adoption as "redesign the process, then apply AI" tend to be mid-transformation, which is exactly when security architecture needs to be in the room early rather than reviewing a fait accompli.
- **Multi-line PHI/PII overlap** — a health or benefits line of business alongside wealth/retirement means some customer records carry PHI-adjacent data even though the primary product is financial, which changes the data classification and the applicable regulation.

> **ℹ This chapter is a starting point, not a finished profile**
>
> Treat the stack table above as the default assumption for a Microsoft-shop financial institution and the confirmation checklist as the discovery work every real engagement still needs to do. The reference architecture, threat model, and priorities in Ch. 18–22 are built to hold regardless of which specific firm you point them at.
