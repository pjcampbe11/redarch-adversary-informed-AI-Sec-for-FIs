"""RedArch — Adversary-Informed AI Security Architecture for Financial Services.

A runnable framework that ties four disciplines together:

    redteam     offensive test harness (probes for the OWASP LLM Top 10 / MITRE ATLAS)
    threatmodel AI-specific threat model generated from a declarative system spec
    controls    controls-as-code policy engine (guardrails as testable assertions)
    report      unified findings/threat/control reporting

The design goal is that *breaking* the system (redteam) and *governing* it
(threatmodel + controls) share one data model, so an offensive finding maps
directly to the control that should have stopped it.
"""

__version__ = "0.1.0"

from redarch.models import Finding, Severity, Threat, ControlResult  # noqa: E402

__all__ = ["Finding", "Severity", "Threat", "ControlResult", "__version__"]
