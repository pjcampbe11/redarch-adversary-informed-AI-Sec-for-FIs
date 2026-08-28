from __future__ import annotations

import json
from typing import Any

from redarch.models import ControlResult, Finding, Threat


def to_json(obj: Any) -> str:
    def default(o):
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return str(o)
    return json.dumps(obj, indent=2, default=default)


_SEV_ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}


def render_findings_md(bundle: dict) -> str:
    s = bundle["summary"]
    lines = [
        f"# RedArch — Offensive Assessment: `{bundle['target']}`",
        "",
        f"**Grade:** {s['grade']}  |  **Probes:** {s['total_probes']}  "
        f"|  **Triggered:** {s['triggered']}  |  **Exposure:** {s['exposure_pct']}%",
        "",
        "| Severity | Triggered |",
        "|---|---|",
    ]
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        lines.append(f"| {_SEV_ICON[sev]} {sev} | {s['by_severity'].get(sev, 0)} |")
    lines += ["", "## Findings", ""]

    for f in bundle["findings"]:
        icon = _SEV_ICON.get(f["severity"], "")
        status = "TRIGGERED" if f["triggered"] else "not triggered"
        lines += [
            f"### {icon} {f['title']}  ({status})",
            f"- **Probe:** `{f['probe_id']}`  ",
            f"- **OWASP LLM:** {', '.join(f['owasp']) or '—'}  |  "
            f"**MITRE ATLAS:** {', '.join(f['atlas']) or '—'}  ",
            f"- **Severity:** {f['severity']}  ",
            f"- {f['detail']}  ",
        ]
        if f["triggered"] and f.get("remediation"):
            lines.append(f"- **Remediation:** {f['remediation']}  ")
        ev = (f.get("evidence") or {}).get("response", "")
        if ev:
            lines += ["", "```", ev.strip()[:400], "```", ""]
    return "\n".join(lines) + "\n"


def render_threatmodel_md(system: str, threats: list[Threat]) -> str:
    lines = [f"# RedArch — Threat Model: {system}", "",
             f"Generated {len(threats)} threats.", "",
             "| ID | Component | Threat | Tactic | OWASP | Severity |",
             "|---|---|---|---|---|---|"]
    for t in threats:
        lines.append(
            f"| {t.id} | {t.component} | {t.title} | {t.tactic} | "
            f"{', '.join(t.owasp)} | {t.severity} |"
        )
    lines += ["", "## Detail", ""]
    for t in threats:
        lines += [
            f"### {t.id} — {t.title}",
            f"- **Component:** {t.component}  |  **Tactic:** {t.tactic}  "
            f"|  **Severity:** {t.severity}  ",
            f"- **OWASP LLM:** {', '.join(t.owasp)}  ",
            f"- {t.description}  ",
            f"- **Recommended controls:** {', '.join(t.recommended_controls)}  ",
            "",
        ]
    return "\n".join(lines) + "\n"


def render_controls_md(policy_name: str, results: list[ControlResult]) -> str:
    passed = sum(1 for r in results if r.passed)
    lines = [
        f"# RedArch — Controls-as-Code: {policy_name}",
        "",
        f"**{passed}/{len(results)} controls passed.**",
        "",
        "| Control | Result | Severity | OWASP | Detail |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        mark = "✅ pass" if r.passed else "❌ FAIL"
        lines.append(
            f"| {r.control_id} — {r.title} | {mark} | {r.severity} | "
            f"{', '.join(r.owasp)} | {r.detail} |"
        )
    return "\n".join(lines) + "\n"
