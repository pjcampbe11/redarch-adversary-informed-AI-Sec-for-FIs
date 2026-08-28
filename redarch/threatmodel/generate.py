"""Rule-based threat-model generator.

Input is a small YAML description of the AI system (components, the data they
touch, tools they can call, exposure). Output is a list of ``Threat`` objects
mapped to MITRE ATLAS tactics and the OWASP LLM Top 10, each with recommended
controls. This is deliberately transparent (a readable rule table, not a model)
so architects can audit *why* a threat was raised.
"""
from __future__ import annotations

from typing import Any

from redarch.models import Severity, Threat

# ---- rule table ---------------------------------------------------------
# Each rule: predicate over a component -> a threat template.
# Keyed loosely on component 'type', 'data', 'tools', 'internet_exposed'.


def _t(idx, comp, title, tactic, owasp, sev, desc, controls):
    return Threat(
        id=f"TM-{idx:03d}",
        title=title,
        component=comp,
        tactic=tactic,
        owasp=owasp,
        severity=Severity.parse(sev),
        description=desc,
        recommended_controls=controls,
    )


def generate_threat_model(spec: dict[str, Any]) -> list[Threat]:
    threats: list[Threat] = []
    idx = 1
    components = spec.get("components", [])

    for comp in components:
        name = comp.get("name", "unnamed")
        ctype = comp.get("type", "llm_app")
        data = set(comp.get("data", []))
        tools = comp.get("tools", []) or []
        exposed = bool(comp.get("internet_exposed", False))
        untrusted_input = bool(comp.get("untrusted_input", exposed))

        if ctype in ("llm_app", "agent", "rag"):
            threats.append(_t(idx, name,
                "Direct prompt injection overriding instructions",
                "Defense Evasion", ["LLM01"], "high",
                "User-supplied text is interpreted as instructions, overriding the "
                "system prompt and policy.",
                ["Instruction/data separation", "Input firewall", "Output policy check"]))
            idx += 1

        if ctype in ("rag", "agent"):
            threats.append(_t(idx, name,
                "Indirect prompt injection via retrieved/tool content",
                "Initial Access", ["LLM01", "LLM08"], "critical",
                "Malicious instructions embedded in retrieved documents, CRM notes, "
                "or web/tool output are executed by the model.",
                ["Content firewall on retrieval", "Sign/scope sources",
                 "Strip instructions from documents", "Constrain tool authorisation"]))
            idx += 1
            threats.append(_t(idx, name,
                "RAG/data-store poisoning",
                "Resource Development", ["LLM04", "LLM08"], "high",
                "Adversary writes poisoned content into an ingested source so future "
                "retrievals bias or hijack responses.",
                ["Provenance + integrity on ingestion", "Source allow-listing",
                 "Embedding anomaly monitoring"]))
            idx += 1

        if tools:
            threats.append(_t(idx, name,
                f"Excessive agency via tools ({', '.join(tools)})",
                "Impact", ["LLM06"], "critical",
                "The model can invoke state-changing tools; a successful injection or "
                "jailbreak converts directly into unauthorised action.",
                ["Human-in-the-loop for state changes", "Least-privilege tool scopes",
                 "Per-transaction limits + step-up auth outside the model"]))
            idx += 1

        if data & {"pii", "financial", "phi", "confidential"}:
            threats.append(_t(idx, name,
                "Sensitive data disclosure",
                "Exfiltration", ["LLM02"], "critical",
                "Sensitive records reachable by the model can be surfaced to an "
                "unauthorised user (broken object-level authorisation at retrieval).",
                ["Per-user row-level entitlements at retrieval", "PII tokenisation/redaction",
                 "Output DLP"]))
            idx += 1

        if untrusted_input:
            threats.append(_t(idx, name,
                "System prompt / configuration leakage",
                "Discovery", ["LLM07"], "medium",
                "The system prompt (and anything embedded in it) is recoverable by an "
                "attacker.",
                ["No secrets in prompts", "Assume prompt is public", "Rotate any leaked tokens"]))
            idx += 1

        if exposed:
            threats.append(_t(idx, name,
                "Unbounded consumption / model denial-of-wallet",
                "Impact", ["LLM10"], "medium",
                "Uncapped requests drive cost and latency; adversary can exhaust quota "
                "or budget.",
                ["Rate limiting + quotas", "Cost anomaly alerts", "Input size caps"]))
            idx += 1

        if ctype in ("model_endpoint", "training"):
            threats.append(_t(idx, name,
                "Model theft / extraction",
                "Exfiltration", ["LLM10"], "high",
                "Query-based extraction or exposed weights let an adversary clone the "
                "model or recover training data.",
                ["Rate limiting + watermarking", "Access control on weights/registry",
                 "Egress monitoring"]))
            idx += 1

        if ctype in ("training", "data_pipeline"):
            threats.append(_t(idx, name,
                "Training-data poisoning",
                "Persistence", ["LLM04"], "high",
                "Poisoned training/fine-tuning data plants backdoors or biases in the "
                "deployed model.",
                ["Dataset provenance + signing", "Poisoning/outlier detection",
                 "Reproducible, gated training pipelines"]))
            idx += 1

    return threats


def load_spec(path: str) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
