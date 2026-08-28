"""RedArch command line.

    redarch redteam    --target examples/targets/mock.yaml [--pack pack.yaml]
    redarch threatmodel --spec examples/voya_wealth_advisor.yaml
    redarch controls    --spec examples/voya_wealth_advisor.yaml --policy policies/finserv-genai.yaml
    redarch assess      --spec ... --policy ... --target ...   # all three + posture

Everything writes Markdown to stdout by default; add --json for machine output,
and --out DIR to also drop report files.
"""
from __future__ import annotations

import argparse
import os
import sys

from redarch.controls import evaluate_policy, load_policy
from redarch.redteam.harness import run_suite
from redarch.report import (
    render_controls_md,
    render_findings_md,
    render_threatmodel_md,
    to_json,
)
from redarch.targets import build_target
from redarch.threatmodel import generate_threat_model, load_spec


def _load_yaml(path):
    import yaml
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _emit(text: str, out_dir, filename, json_mode=False, payload=None):
    body = to_json(payload) if json_mode and payload is not None else text
    sys.stdout.write(body if body.endswith("\n") else body + "\n")
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        name = filename.replace(".md", ".json") if json_mode else filename
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
            fh.write(body)


def cmd_redteam(args):
    target = build_target(_load_yaml(args.target) if args.target else {"type": "mock"})
    bundle = run_suite(target, packs=args.pack or [])
    bundle.pop("_findings_objs", None)
    _emit(render_findings_md(bundle), args.out, "redteam.md", args.json, bundle)
    return 1 if bundle["summary"]["triggered"] and args.fail_on_finding else 0


def cmd_threatmodel(args):
    spec = load_spec(args.spec)
    threats = generate_threat_model(spec)
    _emit(render_threatmodel_md(spec.get("system", "system"), threats),
          args.out, "threatmodel.md", args.json, threats)
    return 0


def cmd_controls(args):
    spec = load_spec(args.spec)
    policy = load_policy(args.policy)
    results = evaluate_policy(spec, policy)
    _emit(render_controls_md(policy.get("policy", "policy"), results),
          args.out, "controls.md", args.json, results)
    failed = [r for r in results if not r.passed]
    return 1 if failed and args.fail_on_violation else 0


def cmd_assess(args):
    rc = 0
    rc |= cmd_threatmodel(args)
    rc |= cmd_controls(args)
    rc |= cmd_redteam(args)
    return rc


def build_parser():
    # Common options usable either before OR after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    common.add_argument("--out", help="also write report files to this directory")

    # Note: common options live on each subparser (use them *after* the
    # subcommand), which avoids argparse's parent/child default-clobber gotcha.
    p = argparse.ArgumentParser(
        prog="redarch",
        description="Adversary-informed AI security framework",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    rt = sub.add_parser("redteam", parents=[common], help="run offensive probe suite against a target")
    rt.add_argument("--target", help="target YAML (default: built-in mock)")
    rt.add_argument("--pack", action="append", help="extra probe pack YAML (repeatable)")
    rt.add_argument("--fail-on-finding", action="store_true")
    rt.set_defaults(func=cmd_redteam)

    tm = sub.add_parser("threatmodel", parents=[common], help="generate a threat model from a system spec")
    tm.add_argument("--spec", required=True)
    tm.set_defaults(func=cmd_threatmodel)

    ct = sub.add_parser("controls", parents=[common], help="evaluate controls-as-code policy against a spec")
    ct.add_argument("--spec", required=True)
    ct.add_argument("--policy", required=True)
    ct.add_argument("--fail-on-violation", action="store_true")
    ct.set_defaults(func=cmd_controls)

    ass = sub.add_parser("assess", parents=[common], help="threat model + controls + red team in one run")
    ass.add_argument("--spec", required=True)
    ass.add_argument("--policy", required=True)
    ass.add_argument("--target", help="target YAML (default: built-in mock)")
    ass.add_argument("--pack", action="append")
    ass.add_argument("--fail-on-finding", action="store_true")
    ass.add_argument("--fail-on-violation", action="store_true")
    ass.set_defaults(func=cmd_assess)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
