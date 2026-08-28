"""Declarative selectors and assertions used by the policy engine."""
from __future__ import annotations

from typing import Any


def matches(component: dict, selector: dict) -> bool:
    """Does this component fall under the control's scope?"""
    if not selector or selector.get("any"):
        return True
    if "type" in selector and component.get("type") != selector["type"]:
        return False
    if "has_tool" in selector:
        if selector["has_tool"] not in (component.get("tools") or []):
            return False
    if "has_data" in selector:
        if selector["has_data"] not in (component.get("data") or []):
            return False
    if "internet_exposed" in selector:
        if bool(component.get("internet_exposed", False)) != bool(selector["internet_exposed"]):
            return False
    return True


def assertion_holds(component: dict, assertion: dict) -> tuple[bool, str]:
    """Return (passed, human-readable reason)."""
    if "field" in assertion:
        field = assertion["field"]
        default = assertion.get("default")
        actual = component.get(field, default)
        if "equals" in assertion:
            ok = actual == assertion["equals"]
            return ok, f"{field}={actual!r} (want {assertion['equals']!r})"
        if "not_equals" in assertion:
            ok = actual != assertion["not_equals"]
            return ok, f"{field}={actual!r} (must not be {assertion['not_equals']!r})"
        return actual is not None, f"{field}={actual!r} (must be set)"

    if "control_present" in assertion:
        want = assertion["control_present"]
        present = want in (component.get("controls") or [])
        return present, f"control {want!r} {'present' if present else 'MISSING'}"

    if "forbid_field" in assertion:
        field = assertion["forbid_field"]
        present = bool(component.get(field, False))
        return (not present), f"{field}={present!r} (must be absent/false)"

    return False, "unknown assertion"
