"""The runner: point a suite of probes at a target, collect findings."""
from __future__ import annotations

from typing import Optional

from redarch.models import Finding, sort_by_severity
from redarch.redteam.probes import Probe, build_default_suite, load_pack
from redarch.redteam.scoring import summarize
from redarch.targets.base import Target


class Harness:
    def __init__(self, target: Target, suite: Optional[list[Probe]] = None):
        self.target = target
        self.suite = suite if suite is not None else build_default_suite()

    def add_pack(self, path: str) -> "Harness":
        self.suite.extend(load_pack(path))
        return self

    def run(self) -> list[Finding]:
        findings = [probe.run(self.target) for probe in self.suite]
        return sort_by_severity(findings)


def run_suite(
    target: Target,
    packs: Optional[list[str]] = None,
) -> dict:
    """Convenience: run default suite (+ optional packs) and return a bundle."""
    harness = Harness(target)
    for p in packs or []:
        harness.add_pack(p)
    findings = harness.run()
    return {
        "target": target.name,
        "summary": summarize(findings),
        "findings": [f.to_dict() for f in findings],
        "_findings_objs": findings,  # kept for in-process reporting
    }
