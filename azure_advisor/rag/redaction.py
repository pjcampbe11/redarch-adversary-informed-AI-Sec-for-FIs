"""
redaction.py — tokenize/redact PII before it reaches the model.

Field guide: Ch. 07 (defense: "PII tokenization/redaction before the model").

WHY BEFORE THE MODEL
Even entitled data should be minimized. The model needs to reason about an
account, not memorize its owner's SSN. We replace sensitive spans with masked
tokens so a leak (or a log line) exposes nothing usable. This complements — does
not replace — the retrieval-time entitlement in retrieval.py.

This is a deterministic local pass. In production you'd back it with Azure AI
Language PII detection for broader coverage; the regexes here are the fast,
dependency-free floor.
"""
from __future__ import annotations

import re

_PATTERNS = [
    (re.compile(r"\b(\d{3})-(\d{2})-(\d{4})\b"), lambda m: f"***-**-{m.group(3)}"),  # SSN → keep last 4
    (re.compile(r"\b(\d{12,19})\b"), lambda m: "•" * (len(m.group(1)) - 4) + m.group(1)[-4:]),  # card/acct
]


def redact_pii(text: str) -> str:
    """Return `text` with SSNs and long numeric identifiers masked to last-4."""
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out
