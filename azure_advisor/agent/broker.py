"""
broker.py — the action broker: where agency is gated.

Field guide: Ch. 08 (excessive agency, the #1 crown jewel).

CONTRACT
The model can only REQUEST a tool call. The broker decides the outcome:

    EXECUTED         → low-risk, in-scope, within limits (e.g. get_balance)
    NEEDS_APPROVAL   → irreversible/high-value/external → human-in-the-loop
    DENIED           → out of the caller's scope, or policy violation

Every decision is made from the CALLER's identity and POLICY (config), never from
the model's text. A poisoned document that makes the model emit transfer_funds
lands here and stops — it can't satisfy the human-approval + scope requirements.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from azure_advisor.agent.tools import READ_TIER, WRITE_TIER
from azure_advisor.config import SETTINGS


class Decision(enum.Enum):
    EXECUTED = "executed"
    NEEDS_APPROVAL = "needs_approval"
    DENIED = "denied"


@dataclass
class BrokerOutcome:
    decision: Decision
    tool: str
    detail: str = ""
    approval_id: Optional[str] = None
    result: Any = None


class ActionBroker:
    """Authorizes tool calls out of band from the model.

    Args:
        caller_id: the authenticated user (from the OBO'd identity).
        caller_scopes: capabilities the caller actually holds (RBAC/entitlements).
        executor: optional callable(tool, args) -> result that performs an
                  APPROVED, in-scope action. In demo/tests this is a stub; in
                  prod it calls the real ledger service (which re-checks auth).
    """

    def __init__(self, caller_id: str, caller_scopes: set[str],
                 executor: Optional[Callable[[str, dict], Any]] = None):
        self.caller_id = caller_id
        self.caller_scopes = caller_scopes
        self.executor = executor or (lambda tool, args: {"stub": True})

    def handle(self, tool: str, args: dict) -> BrokerOutcome:
        # 1) Unknown tool → deny (never execute something not in the schema).
        if tool not in READ_TIER and tool not in WRITE_TIER:
            return BrokerOutcome(Decision.DENIED, tool, "unknown tool")

        # 2) Scope check: does the CALLER hold the capability? (least privilege)
        needed_scope = f"tool:{tool}"
        if needed_scope not in self.caller_scopes:
            return BrokerOutcome(Decision.DENIED, tool,
                                 f"caller lacks scope {needed_scope}")

        # 3) Read tier: low risk, in scope → execute directly.
        if tool in READ_TIER:
            return BrokerOutcome(Decision.EXECUTED, tool, "read-tier in scope",
                                 result=self.executor(tool, args))

        # 4) Write tier (transfer_funds): apply money-movement policy.
        if tool == "transfer_funds":
            amount = float(args.get("amount_usd", 0) or 0)
            external = bool(args.get("destination_is_external", False))
            # External destinations always need a human; high-value too.
            if (external and SETTINGS.external_transfer_needs_approval) \
               or amount > SETTINGS.transfer_auto_limit_usd:
                approval_id = str(uuid.uuid4())
                # Stage the request for a human approver + step-up auth. It does
                # NOT execute here — that happens only after approval elsewhere.
                return BrokerOutcome(
                    Decision.NEEDS_APPROVAL, tool,
                    f"amount=${amount:g} external={external}: human approval + "
                    f"step-up required", approval_id=approval_id)
            # Within auto-limit AND internal → execute (still out-of-band).
            return BrokerOutcome(Decision.EXECUTED, tool, "within policy",
                                 result=self.executor(tool, args))

        return BrokerOutcome(Decision.DENIED, tool, "no policy path")  # default deny
