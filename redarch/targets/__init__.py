"""Target adapters — the thing under test.

A Target is anything that turns a prompt into text: a raw model endpoint, a
RAG assistant, or an agent. Probes are written against this interface so the
same probe pack runs against a local mock, an Azure OpenAI deployment, or any
OpenAI-compatible gateway (vLLM, Ollama, LiteLLM, etc.).
"""
from redarch.targets.base import Target, TargetResponse
from redarch.targets.mock import MockAdvisorTarget
from redarch.targets.openai_compat import OpenAICompatTarget

__all__ = [
    "Target",
    "TargetResponse",
    "MockAdvisorTarget",
    "OpenAICompatTarget",
    "build_target",
]


def build_target(spec: dict) -> Target:
    """Factory: ``{"type": "mock"}`` / ``{"type": "openai_compat", ...}``."""

    kind = (spec or {}).get("type", "mock")
    if kind == "mock":
        return MockAdvisorTarget(**{k: v for k, v in spec.items() if k != "type"})
    if kind in ("openai_compat", "azure_openai", "openai"):
        return OpenAICompatTarget(**{k: v for k, v in spec.items() if k != "type"})
    raise ValueError(f"unknown target type: {kind!r}")
