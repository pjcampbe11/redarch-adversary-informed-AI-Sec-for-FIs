from __future__ import annotations

from typing import Any

from redarch.models import ControlResult, Severity
from redarch.controls.checks import assertion_holds, matches


def evaluate_policy(spec: dict[str, Any], policy: dict[str, Any]) -> list[ControlResult]:
    """Evaluate every control against every in-scope component.

    A control passes iff *all* in-scope components satisfy its assertion. A
    control with no in-scope components is reported as passed (not applicable),
    with a note — so gaps are visible without inflating failures.
    """
    results: list[ControlResult] = []
    components = spec.get("components", [])

    for ctrl in policy.get("controls", []):
        selector = ctrl.get("applies_to", {"any": True})
        assertion = ctrl.get("assert", {})
        severity = Severity.parse(ctrl.get("severity", "medium"))
        owasp = list(ctrl.get("owasp", []))

        in_scope = [c for c in components if matches(c, selector)]
        if not in_scope:
            results.append(ControlResult(
                control_id=ctrl["id"], title=ctrl.get("title", ctrl["id"]),
                passed=True, severity=severity, owasp=owasp,
                detail="not applicable (no in-scope components)",
            ))
            continue

        failures = []
        for comp in in_scope:
            ok, reason = assertion_holds(comp, assertion)
            if not ok:
                failures.append(f"{comp.get('name', '?')}: {reason}")

        results.append(ControlResult(
            control_id=ctrl["id"], title=ctrl.get("title", ctrl["id"]),
            passed=not failures, severity=severity, owasp=owasp,
            detail=("; ".join(failures) if failures
                    else f"satisfied by {len(in_scope)} component(s)"),
        ))

    return results


def load_policy(path: str) -> dict:
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
