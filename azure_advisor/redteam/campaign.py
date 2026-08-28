"""
campaign.py — run the REAL multi-agent harness against the Azure OpenAI target.

Field guide: Ch. 03/04. This is wired to `pjcampbe11/multi-agent-harness`
(package `xteaming`): Planner → Attacker → Verifier → TextGrad Optimizer, driven
by `xteaming.orchestrator.Orchestrator`.

HOW THE WIRING WORKS
* The harness talks to every role through `xteaming.llm.LLMClient.chat(messages)`.
* We attack our OWN Azure OpenAI deployment. Rather than force the harness's raw
  OpenAI client to speak Azure's api-version/api-key dialect, we hand it a small
  duck-typed client (`AzureOpenAILLMClient`) whose `.chat()` routes to our keyless
  `AoaiClient` (managed identity, correct api-version). So the harness attacks the
  real deployment through the real auth path.
* Attacker / Verifier / Planner / Optimizer run on ordinary OpenAI-compatible
  models via the harness's own `LLMClient`. Role independence is enforced:
  Verifier model MUST differ from the Target.

INSTALLING THE HARNESS
It's a source checkout (no PyPI package). Either:
  * `pip install -e /path/to/multi-agent-harness` (if it has a setup), or
  * clone it and set `XTEAMING_PATH=/path/to/multi-agent-harness` — this module
    adds that path to sys.path automatically.

AUTHORIZATION
`run_campaign(..., authorized=True)` is mandatory; the Orchestrator refuses to run
otherwise. Objectives come from YOUR authorized benchmark file (JSONL) — none ship
here.

    python -m azure_advisor.redteam.campaign \
        --objectives examples/advisor_scope.jsonl \
        --target-deployment advisor-gpt4o \
        --attacker gpt-4o-mini --verifier gpt-4o \
        --authorized
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional

from azure_advisor.aoai.target import classify_platform_block
from azure_advisor.rag.grounding import ADVISOR_SYSTEM_PROMPT


# --------------------------------------------------------------------------- #
# 1. The Azure target as an LLMClient the harness can drive.                    #
# --------------------------------------------------------------------------- #
class AzureOpenAILLMClient:
    """Duck-typed `xteaming.llm.LLMClient`: exposes `.chat(messages, config=None)
    -> str`, routing to our keyless AoaiClient. This is what the harness's
    Attacker calls turn-by-turn.

    `client` is injectable so this is unit-testable without Azure or the SDK.
    """

    def __init__(self, deployment: Optional[str] = None, client: Any = None):
        from azure_advisor.config import SETTINGS

        self.model = f"azure:{deployment or SETTINGS.aoai_deployment}"
        if client is not None:
            self._client = client
        else:
            from azure_advisor.aoai.client import AoaiClient
            self._client = AoaiClient(deployment)

    def chat(self, messages: list[dict], config: Any = None) -> str:
        # Map the harness's GenerationConfig (if any) to our temperature knob.
        temperature = float(getattr(config, "temperature", 0.7) or 0.7)
        try:
            return self._client.chat(messages, temperature=temperature).text
        except Exception as exc:
            # Azure content-filter block is a PLATFORM block, not a model refusal
            # (Ch. 04 gotcha). Return a labeled sentinel so transcripts/analysis
            # can separate it from genuine model robustness. Re-raise anything else.
            if classify_platform_block(exc):
                return "[platform_block] request blocked by Azure content filter"
            raise


# --------------------------------------------------------------------------- #
# 2. Import the real harness (with a helpful message if it isn't installed).    #
# --------------------------------------------------------------------------- #
@dataclass
class _Xteaming:
    Orchestrator: Any
    LLMClient: Any
    Objective: Any
    PlannerConfig: Any
    RunConfig: Any


def _import_xteaming() -> _Xteaming:
    # Allow a source checkout to be used without installation.
    extra = os.environ.get("XTEAMING_PATH")
    if extra and extra not in sys.path:
        sys.path.insert(0, extra)

    try:
        from xteaming.orchestrator import Orchestrator
        from xteaming.llm import LLMClient
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "The 'xteaming' harness is not importable. Install it with "
            "`pip install -e /path/to/multi-agent-harness`, or set "
            "XTEAMING_PATH=/path/to/multi-agent-harness. Original error: " + str(exc)
        ) from exc

    # Config/schema locations differ slightly across revisions — resolve defensively.
    Objective = _first_import([
        ("xteaming.schemas", "Objective"),
        ("xteaming.orchestrator", "Objective"),
    ])
    PlannerConfig = _first_import([
        ("xteaming.orchestrator", "PlannerConfig"),
        ("xteaming.schemas", "PlannerConfig"),
        ("xteaming.config", "PlannerConfig"),
    ])
    RunConfig = _first_import([
        ("xteaming.orchestrator", "RunConfig"),
        ("xteaming.schemas", "RunConfig"),
        ("xteaming.config", "RunConfig"),
    ])
    return _Xteaming(Orchestrator, LLMClient, Objective, PlannerConfig, RunConfig)


def _first_import(candidates: list[tuple[str, str]]):
    last = None
    for module, name in candidates:
        try:
            mod = __import__(module, fromlist=[name])
            return getattr(mod, name)
        except (ImportError, AttributeError) as exc:
            last = exc
    raise ImportError(f"could not locate {candidates[0][1]} in xteaming: {last}")


# --------------------------------------------------------------------------- #
# 3. Objectives loader (JSONL: {"text": ..., "category": ...}).                 #
# --------------------------------------------------------------------------- #
def load_objectives(path: str, Objective: Any) -> list:
    """Parse an authorized-benchmark JSONL file into harness Objective objects."""
    objectives = []
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            objectives.append(_make_objective(Objective, i, row))
    if not objectives:
        raise ValueError(f"no objectives parsed from {path}")
    return objectives


def _make_objective(Objective: Any, idx: int, row: dict):
    """Objective's exact fields vary; construct tolerantly (id/text/category)."""
    kwargs = {"text": row.get("text", row.get("objective", ""))}
    if "category" in row:
        kwargs["category"] = row["category"]
    for id_field in ("id", "objective_id"):
        try:
            return Objective(**{id_field: f"obj-{idx}"}, **kwargs)
        except TypeError:
            continue
    return Objective(**kwargs)  # some revisions auto-assign ids


# --------------------------------------------------------------------------- #
# 4. Run the campaign.                                                          #
# --------------------------------------------------------------------------- #
def run_campaign(
    objectives_path: str,
    *,
    authorized: bool = False,
    target_deployment: str = "advisor-gpt4o",
    attacker_model: str = "gpt-4o-mini",
    verifier_model: str = "gpt-4o",
    n_plans: int = 20,
    max_plans: int = 5,
    min_diversity: float = 0.702,
    out_dir: str = "runs",
    target_system_prompt: Optional[str] = None,
) -> dict:
    """Run the real X-Teaming loop against the Azure OpenAI deployment.

    Returns a summary dict (run dir, transcript count, target/verifier used).
    """
    if not authorized:
        raise PermissionError("run_campaign requires authorized=True (written scope).")

    # Role independence: the verifier must not be the target (no self-grading).
    if verifier_model.strip().lower() in {target_deployment.strip().lower(),
                                          f"azure:{target_deployment}".lower()}:
        raise ValueError("Verifier model must differ from the Target (no self-grading).")

    X = _import_xteaming()

    # The Azure deployment, wrapped so the harness can drive it.
    target_llm = AzureOpenAILLMClient(target_deployment)

    # Attacker / Verifier on ordinary OpenAI-compatible models (harness's client).
    attacker_llm = X.LLMClient(model=attacker_model)
    verifier_llm = X.LLMClient(model=verifier_model)

    orch = X.Orchestrator(
        attacker_llm=attacker_llm,
        target_llm=target_llm,
        verifier_llm=verifier_llm,
        target_system_prompt=target_system_prompt or ADVISOR_SYSTEM_PROMPT,
        planner_config=X.PlannerConfig(n_plans=n_plans, min_diversity=min_diversity),
        run_config=X.RunConfig(output_dir=out_dir, max_plans_per_objective=max_plans),
        authorized=True,
    )

    objectives = load_objectives(objectives_path, X.Objective)
    transcripts = orch.run(objectives)

    return {
        "target": target_llm.model,
        "attacker": attacker_model,
        "verifier": verifier_model,
        "objectives": len(objectives),
        "transcripts": len(transcripts),
        "out_dir": out_dir,
    }


# --------------------------------------------------------------------------- #
# 5. CLI.                                                                       #
# --------------------------------------------------------------------------- #
def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        prog="azure_advisor.redteam.campaign",
        description="Run the X-Teaming multi-agent harness against an Azure OpenAI deployment.",
    )
    p.add_argument("--objectives", required=True, help="authorized-benchmark JSONL")
    p.add_argument("--target-deployment", default="advisor-gpt4o")
    p.add_argument("--attacker", default="gpt-4o-mini")
    p.add_argument("--verifier", default="gpt-4o")
    p.add_argument("--n-plans", type=int, default=20)
    p.add_argument("--max-plans", type=int, default=5)
    p.add_argument("--min-diversity", type=float, default=0.702)
    p.add_argument("--out", default="runs")
    p.add_argument("--authorized", action="store_true",
                   help="required; you confirm written authorization to test the target")
    args = p.parse_args(argv)

    summary = run_campaign(
        args.objectives, authorized=args.authorized,
        target_deployment=args.target_deployment,
        attacker_model=args.attacker, verifier_model=args.verifier,
        n_plans=args.n_plans, max_plans=args.max_plans,
        min_diversity=args.min_diversity, out_dir=args.out,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
