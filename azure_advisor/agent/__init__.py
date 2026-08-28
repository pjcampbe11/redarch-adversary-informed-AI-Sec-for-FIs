"""
agent/ — tools and the action broker (excessive-agency control).

Field guide: Ch. 08 (agent tool-abuse) and Ch. 12 (Copilot Studio actions).

  tools.py  → the tool SCHEMAS the model may request (read vs. write tiers).
  broker.py → the gate that decides whether a requested call executes. The model
              can REQUEST; only the broker EXECUTES — with human-in-the-loop and
              step-up auth for irreversible/high-value actions.

If a successful injection ever reaches a tool call, this is the layer that makes
it a non-event.
"""
from azure_advisor.agent.broker import ActionBroker, BrokerOutcome
from azure_advisor.agent.tools import TOOLS

__all__ = ["ActionBroker", "BrokerOutcome", "TOOLS"]
