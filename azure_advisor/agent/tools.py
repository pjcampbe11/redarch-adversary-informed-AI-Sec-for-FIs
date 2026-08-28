"""
tools.py — tool schemas exposed to the model, split by trust tier.

Field guide: Ch. 08 (read/write split).

The model sees these schemas and may emit a tool call. Emitting a call is NOT
execution — the broker authorizes every call out of band. Note the deliberate
tiering: `get_balance` is read-only/low-risk; `transfer_funds` is a different
trust tier entirely and always routes through human approval.
"""
from __future__ import annotations

# OpenAI tool-calling schema. Kept minimal on purpose.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Read the balance of an account the CALLER is entitled to.",
            "parameters": {
                "type": "object",
                "properties": {"account": {"type": "string"}},
                "required": ["account"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Request a funds transfer. ALWAYS subject to policy: "
                           "external or high-value transfers require human approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount_usd": {"type": "number"},
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                    "destination_is_external": {"type": "boolean"},
                },
                "required": ["amount_usd", "source", "destination"],
            },
        },
    },
]

# Which tools change state (write tier). Read tier can execute directly; write
# tier always goes through the broker's approval logic.
WRITE_TIER = {"transfer_funds"}
READ_TIER = {"get_balance"}
