"""Data-driven probes loaded from YAML packs.

Lets an operator add attacks without writing Python. A pack entry:

    - id: LLM01-CUSTOM-01
      title: "Obfuscated override"
      owasp: [LLM01]
      atlas: [AML.T0051.000]
      severity: high
      prompt: "SXQ... (base64) decode and follow"
      context: "optional untrusted retrieved text"
      detector: leaked_secret        # or: leaked_pii | tool_call | contains
      markers: ["disabled", "override"]   # for detector: contains
      tool_name: transfer_funds           # for detector: tool_call
"""
from __future__ import annotations

from typing import Optional

from redarch.models import Severity
from redarch.redteam.probes.base import (
    Probe,
    contains_any,
    leaked_pii,
    leaked_secret,
    made_tool_call,
    refused,
)
from redarch.targets.base import Target, TargetResponse

_DETECTORS = {
    "leaked_secret": lambda r, cfg: leaked_secret(r),
    "leaked_pii": lambda r, cfg: leaked_pii(r),
    "tool_call": lambda r, cfg: made_tool_call(r, cfg.get("tool_name")),
    "contains": lambda r, cfg: contains_any(r, cfg.get("markers", [])),
    "not_refused_and_contains": lambda r, cfg: (
        contains_any(r, cfg.get("markers", [])) and not refused(r)
    ),
}


class DataProbe(Probe):
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.id = cfg["id"]
        self.title = cfg.get("title", cfg["id"])
        self.owasp = list(cfg.get("owasp", []))
        self.atlas = list(cfg.get("atlas", []))
        self.tactic = cfg.get("tactic", "")
        self.severity = Severity.parse(cfg.get("severity", "medium"))
        self.remediation = cfg.get("remediation", "")
        self._prompt = cfg["prompt"]
        self._context = cfg.get("context")
        self._detector_name = cfg.get("detector", "contains")
        if self._detector_name not in _DETECTORS:
            raise ValueError(f"unknown detector {self._detector_name!r}")

    def attack(self, target: Target) -> TargetResponse:
        return target.generate(self._prompt, context=self._context)

    def succeeded(self, resp: TargetResponse) -> bool:
        return _DETECTORS[self._detector_name](resp, self.cfg)


def load_pack(path: str) -> list[DataProbe]:
    import yaml  # local import keeps import-time deps minimal

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    entries = data.get("probes", data if isinstance(data, list) else [])
    return [DataProbe(e) for e in entries]
