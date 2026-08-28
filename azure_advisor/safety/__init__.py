"""
safety/ — the input/output firewall (Azure AI Content Safety).

Field guide: Ch. 05/06 (injection) and Ch. 07 (output DLP).

Two gates wrap the model:
  * INPUT  — Prompt Shields: detect direct jailbreaks AND indirect injection
             hidden in retrieved documents, BEFORE the model sees them.
  * OUTPUT — content moderation + a DLP pass to catch sensitive data
             (SSNs, account numbers) leaking out in the response.

Neither gate is the model. That's the point: the model is untrusted, so the
firewall is deterministic and lives outside it.
"""
from azure_advisor.safety.content_safety import (
    ShieldResult,
    dlp_scan,
    moderate_output,
    shield_input,
)

__all__ = ["ShieldResult", "shield_input", "moderate_output", "dlp_scan"]
