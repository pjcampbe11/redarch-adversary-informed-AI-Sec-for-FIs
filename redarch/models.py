"""Shared data model.

Everything in RedArch speaks in these objects so that an offensive Finding,
a Threat from the threat model, and a ControlResult from the policy engine can
be cross-referenced by their OWASP LLM / MITRE ATLAS tags.
"""
from __future__ import annotations

import dataclasses
import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class Severity(enum.IntEnum):
    """Ordered so findings sort worst-first."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, value: "str | int | Severity") -> "Severity":
        if isinstance(value, Severity):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[str(value).strip().upper()]

    def __str__(self) -> str:  # nicer report output
        return self.name


@dataclass
class Finding:
    """One result from running an offensive probe against a target."""

    probe_id: str
    title: str
    severity: Severity
    triggered: bool
    detail: str = ""
    owasp: list[str] = field(default_factory=list)      # e.g. ["LLM01"]
    atlas: list[str] = field(default_factory=list)      # e.g. ["AML.T0051"]
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["severity"] = str(self.severity)
        return d


@dataclass
class Threat:
    """One entry in a generated threat model."""

    id: str
    title: str
    component: str
    tactic: str            # MITRE ATLAS tactic
    owasp: list[str]
    severity: Severity
    description: str
    recommended_controls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["severity"] = str(self.severity)
        return d


@dataclass
class ControlResult:
    """Outcome of evaluating one controls-as-code assertion."""

    control_id: str
    title: str
    passed: bool
    severity: Severity
    owasp: list[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = dataclasses.asdict(self)
        d["severity"] = str(self.severity)
        return d


def sort_by_severity(items: list[Any]) -> list[Any]:
    """Worst-first ordering for any object exposing a ``.severity``."""

    return sorted(items, key=lambda x: int(x.severity), reverse=True)
