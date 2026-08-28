from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TargetResponse:
    text: str
    tool_calls: list[dict] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class Target(abc.ABC):
    """Interface every adapter implements."""

    #: human label used in reports
    name: str = "target"

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        context: Optional[str] = None,
    ) -> TargetResponse:
        """Return the model's response.

        ``context`` simulates untrusted retrieved content (RAG / tool output),
        which is where indirect prompt injection lives.
        """
        raise NotImplementedError
