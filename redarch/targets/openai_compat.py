"""OpenAI-compatible / Azure OpenAI adapter (stdlib only, no SDK dependency).

Works against:
  * Azure OpenAI       (set base_url to your deployment's chat/completions URL)
  * OpenAI             (https://api.openai.com/v1/chat/completions)
  * Any gateway that speaks the same schema: vLLM, Ollama, LiteLLM, Databricks
    Model Serving foundation-model endpoints, etc.

Kept SDK-free on purpose so the framework has one hard dependency (PyYAML) and
runs in locked-down assessment environments. Network calls only happen when you
actually select this target — the mock target needs neither keys nor egress.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from redarch.targets.base import Target, TargetResponse


class OpenAICompatTarget(Target):
    name = "openai-compat"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        api_key_env: str = "REDARCH_API_KEY",
        auth_header: str = "Authorization",
        auth_prefix: str = "Bearer ",
        extra_headers: Optional[dict] = None,
        timeout: int = 60,
        temperature: float = 0.0,
        **_ignored,
    ):
        self.base_url = base_url or os.environ.get(
            "REDARCH_BASE_URL", "https://api.openai.com/v1/chat/completions"
        )
        self.model = model
        self.api_key = os.environ.get(api_key_env, "")
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix
        self.extra_headers = extra_headers or {}
        self.timeout = timeout
        self.temperature = temperature
        self.name = f"openai-compat:{model}"

    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        context: Optional[str] = None,
    ) -> TargetResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if context:
            # Untrusted retrieved content presented as tool/user content.
            messages.append({"role": "user", "content": f"[RETRIEVED CONTEXT]\n{context}"})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }).encode()

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers[self.auth_header] = f"{self.auth_prefix}{self.api_key}"
        headers.update(self.extra_headers)

        req = urllib.request.Request(self.base_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:  # surface as a benign response
            return TargetResponse(text=f"[target-error] {exc}", raw={"error": str(exc)})

        text = ""
        tool_calls = []
        try:
            choice = data["choices"][0]["message"]
            text = choice.get("content") or ""
            tool_calls = choice.get("tool_calls", []) or []
        except (KeyError, IndexError, TypeError):
            text = json.dumps(data)[:2000]
        return TargetResponse(text=text, tool_calls=tool_calls, raw=data)
