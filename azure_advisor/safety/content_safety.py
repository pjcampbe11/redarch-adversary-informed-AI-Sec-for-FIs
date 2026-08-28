"""
content_safety.py — Prompt Shields (input) + moderation & DLP (output).

Field guide: Ch. 05/06 (prompt injection) and Ch. 07 (RAG exfil / DLP).

WHAT EACH PIECE DOES
* shield_input(user_prompt, documents): calls Azure AI Content Safety
  "Prompt Shields", which flags (a) direct jailbreak attempts in the user prompt
  and (b) INDIRECT injection embedded in retrieved documents. We block on either.
* moderate_output(text): runs the model's answer through content moderation
  (hate/violence/self-harm/sexual categories) before it reaches the user.
* dlp_scan(text): a last-line regex sweep for sensitive identifiers (SSN,
  account numbers) that must never appear in output. Belt-and-suspenders behind
  the retrieval-time entitlement checks in rag/.

FAIL CLOSED
If the safety service errors, treat it as "unsafe" and block — never fail open.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from azure_advisor.config import SETTINGS

# Shapes we never want to see in an outbound message (Ch. 07 output DLP).
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_ACCT = re.compile(r"\b(?:acct|account)[-\s]?\d{4,}\b", re.I)


@dataclass
class ShieldResult:
    blocked: bool
    reason: str = ""
    # which surface tripped it: "user_prompt" (direct) or "document" (indirect)
    source: str = ""


def _client():
    """Lazy Content Safety client (keyless via managed identity)."""
    from azure.ai.contentsafety import ContentSafetyClient
    from azure_advisor.identity.credentials import azure_credential

    return ContentSafetyClient(SETTINGS.content_safety_endpoint, azure_credential())


def shield_input(user_prompt: str, documents: list[str] | None = None) -> ShieldResult:
    """Prompt Shields on the user prompt and any retrieved documents.

    Returns ShieldResult(blocked=True, ...) if an attack is detected on either
    surface. `documents` is where INDIRECT injection hides — always pass the
    retrieved chunks here, not just the user text.
    """
    documents = documents or []
    try:
        from azure.ai.contentsafety.models import ShieldPromptOptions

        resp = _client().shield_prompt(
            options=ShieldPromptOptions(user_prompt=user_prompt, documents=documents)
        )
        # userPromptAnalysis → direct; documentsAnalysis → indirect.
        if getattr(resp.user_prompt_analysis, "attack_detected", False):
            return ShieldResult(True, "jailbreak detected in user prompt", "user_prompt")
        for i, doc in enumerate(resp.documents_analysis or []):
            if getattr(doc, "attack_detected", False):
                return ShieldResult(True, f"indirect injection in document #{i}", "document")
        return ShieldResult(False)
    except Exception as exc:  # fail closed
        return ShieldResult(True, f"content-safety error (failing closed): {exc}", "error")


def moderate_output(text: str) -> ShieldResult:
    """Run the model's answer through content moderation before returning it."""
    try:
        from azure.ai.contentsafety.models import AnalyzeTextOptions

        resp = _client().analyze_text(AnalyzeTextOptions(text=text))
        # Block if any category exceeds a conservative severity threshold.
        for cat in resp.categories_analysis:
            if (cat.severity or 0) >= 4:
                return ShieldResult(True, f"output flagged: {cat.category}", "output")
        return ShieldResult(False)
    except Exception as exc:
        return ShieldResult(True, f"moderation error (failing closed): {exc}", "error")


def dlp_scan(text: str) -> ShieldResult:
    """Deterministic sensitive-data sweep (no service call). Runs even when
    Content Safety is unreachable, so PII can't leak on a safety outage."""
    if _SSN.search(text):
        return ShieldResult(True, "SSN detected in output", "dlp")
    if _ACCT.search(text):
        return ShieldResult(True, "account number detected in output", "dlp")
    return ShieldResult(False)
