"""
client.py — keyless Azure OpenAI chat client with tool-calling.

Field guide: Ch. 04 (adapter) + Ch. 11 (deployments).

DESIGN NOTES
* Auth is keyless via the token provider from identity/credentials.py.
* We expose `chat(...)` returning a small normalized result so the rest of the
  app never depends on the raw SDK shape (api-version drift is contained here).
* `tools` are passed straight through; the model can only REQUEST a tool call —
  it never executes anything. Execution is gated in agent/broker.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from azure_advisor.config import SETTINGS
from azure_advisor.identity.credentials import aoai_token_provider


@dataclass
class ChatResult:
    text: str
    tool_calls: list[dict] = field(default_factory=list)  # [{name, arguments}]
    finish_reason: str = ""
    raw: Any = None


class AoaiClient:
    def __init__(self, deployment: Optional[str] = None):
        self.deployment = deployment or SETTINGS.aoai_deployment
        self._client = None  # built lazily so import needs no SDK/creds

    def _sdk(self):
        if self._client is None:
            from openai import AzureOpenAI  # lazy import

            self._client = AzureOpenAI(
                azure_endpoint=SETTINGS.aoai_endpoint,
                azure_ad_token_provider=aoai_token_provider(),  # keyless
                api_version=SETTINGS.aoai_api_version,           # pin the schema
            )
        return self._client

    def chat(self, messages: list[dict], *, tools: Optional[list[dict]] = None,
             temperature: float = 0.2) -> ChatResult:
        """Send a chat request. `messages` is standard OpenAI format.

        Returns a normalized ChatResult. Note we DON'T act on tool calls here —
        we surface them for the broker to authorize.
        """
        resp = self._sdk().chat.completions.create(
            model=self.deployment, messages=messages,
            tools=tools, temperature=temperature,
        )
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = []
        for tc in (msg.tool_calls or []):
            # Normalize to plain dicts so downstream code is SDK-agnostic.
            import json
            args = tc.function.arguments
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                args = {"_raw": args}
            tool_calls.append({"name": tc.function.name, "arguments": args})
        return ChatResult(
            text=msg.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "",
            raw=resp,
        )
