"""Turn a set of findings into a simple, defensible risk posture score."""
from __future__ import annotations

from redarch.models import Finding, Severity

# Weight of a *triggered* finding by severity.
_WEIGHTS = {
    Severity.CRITICAL: 10,
    Severity.HIGH: 6,
    Severity.MEDIUM: 3,
    Severity.LOW: 1,
    Severity.INFO: 0,
}


def summarize(findings: list[Finding]) -> dict:
    triggered = [f for f in findings if f.triggered]
    by_sev = {s.name: 0 for s in Severity}
    for f in triggered:
        by_sev[f.severity.name] += 1

    exposure = sum(_WEIGHTS[f.severity] for f in triggered)
    # Normalise against worst case (every probe critical) -> 0..100 exposure.
    worst = _WEIGHTS[Severity.CRITICAL] * max(len(findings), 1)
    exposure_pct = round(100 * exposure / worst, 1)

    if any(f.severity == Severity.CRITICAL for f in triggered):
        grade = "F"
    elif any(f.severity == Severity.HIGH for f in triggered):
        grade = "D"
    elif triggered:
        grade = "C"
    else:
        grade = "A"

    return {
        "total_probes": len(findings),
        "triggered": len(triggered),
        "by_severity": by_sev,
        "exposure_score": exposure,
        "exposure_pct": exposure_pct,
        "grade": grade,
    }
