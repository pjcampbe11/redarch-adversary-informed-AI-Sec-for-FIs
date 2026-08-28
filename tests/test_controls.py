from redarch.controls import evaluate_policy

POLICY = {
    "policy": "p",
    "controls": [
        {"id": "C1", "title": "HITL", "severity": "critical", "owasp": ["LLM06"],
         "applies_to": {"has_tool": "transfer_funds"},
         "assert": {"field": "human_in_the_loop", "equals": True, "default": False}},
        {"id": "C2", "title": "entitlements", "severity": "critical", "owasp": ["LLM02"],
         "applies_to": {"type": "rag", "has_data": "pii"},
         "assert": {"control_present": "row_level_entitlements"}},
        {"id": "C3", "title": "no secrets", "severity": "high", "owasp": ["LLM07"],
         "applies_to": {"any": True},
         "assert": {"forbid_field": "secrets_in_prompt"}},
    ],
}


def _spec(**over):
    comp = {"name": "copilot", "type": "agent", "data": ["pii"],
            "tools": ["transfer_funds"], "human_in_the_loop": False,
            "secrets_in_prompt": True, "controls": []}
    comp.update(over)
    return {"components": [comp, {"name": "idx", "type": "rag", "data": ["pii"], "controls": []}]}


def test_insecure_spec_fails_controls():
    results = evaluate_policy(_spec(), POLICY)
    failed = {r.control_id for r in results if not r.passed}
    assert {"C1", "C2", "C3"} <= failed


def test_fixed_spec_passes():
    fixed = {"components": [
        {"name": "copilot", "type": "agent", "data": ["pii"], "tools": ["transfer_funds"],
         "human_in_the_loop": True, "secrets_in_prompt": False, "controls": []},
        {"name": "idx", "type": "rag", "data": ["pii"],
         "controls": ["row_level_entitlements"]},
    ]}
    results = evaluate_policy(fixed, POLICY)
    assert all(r.passed for r in results)


def test_not_applicable_counts_as_pass():
    spec = {"components": [{"name": "x", "type": "model_endpoint", "controls": []}]}
    results = evaluate_policy(spec, POLICY)
    # no tools, no rag, but C3 (any) applies and secrets_in_prompt absent -> pass
    assert all(r.passed for r in results)
