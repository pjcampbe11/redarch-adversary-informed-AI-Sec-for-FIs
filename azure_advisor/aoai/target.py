"""
target.py — the red-team TARGET adapter for the multi-agent harness.

Field guide: Ch. 04 (wiring the harness to Azure).

WHY A SEPARATE ADAPTER
The harness (pjcampbe11/multi-agent-harness) attacks anything exposing a simple
`generate(messages) -> str`. By adapting the REAL AoaiClient we test the true
production path — same keyless auth, same deployment, same content filter — so
findings reflect the system, not a lookalike.

IMPORTANT: this only GENERATES. It cannot move money or read entitled data — the
target is the model, and the model holds no capability (that's the whole design).
"""
from __future__ import annotations

from typing import Optional

from azure_advisor.aoai.client import AoaiClient


class AzureOpenAITarget:
    """OpenAI-compatible target the harness's Attacker drives turn-by-turn."""

    def __init__(self, deployment: Optional[str] = None):
        self.name = f"azure:{deployment or 'advisor-gpt4o'}"
        self._client = AoaiClient(deployment)

    def generate(self, messages: list[dict], temperature: float = 0.7) -> str:
        # High-ish temperature during red teaming to surface non-deterministic
        # failure modes the harness's verifier can then grade.
        return self._client.chat(messages, temperature=temperature).text


# -- Handling the Azure content filter correctly (Ch. 04 gotcha) --------------
# A blocked request raises, with a `content_filter` code — that is a PLATFORM
# block, NOT the model refusing. If you score it as a model refusal you credit
# the model for a guardrail it didn't provide. Classify it separately.
def classify_platform_block(exc: Exception) -> Optional[str]:
    """Return 'platform_block' if `exc` is an Azure content-filter rejection,
    else None. Use this in the harness verifier to avoid inflating robustness."""
    text = str(exc).lower()
    if "content_filter" in text or "content management policy" in text:
        return "platform_block"
    return None
