from redarch.threatmodel import generate_threat_model


SPEC = {
    "system": "t",
    "components": [
        {"name": "copilot", "type": "agent", "data": ["pii"],
         "tools": ["transfer_funds"], "internet_exposed": True},
        {"name": "idx", "type": "rag", "data": ["pii"]},
        {"name": "pipe", "type": "data_pipeline", "data": ["pii"]},
    ],
}


def test_generates_threats():
    threats = generate_threat_model(SPEC)
    assert len(threats) >= 6


def test_tools_yield_excessive_agency():
    titles = [t.title for t in generate_threat_model(SPEC)]
    assert any("Excessive agency" in t for t in titles)


def test_rag_yields_indirect_injection():
    owasp = {o for t in generate_threat_model(SPEC) for o in t.owasp}
    assert "LLM01" in owasp and "LLM04" in owasp


def test_pipeline_yields_poisoning():
    titles = [t.title for t in generate_threat_model(SPEC)]
    assert any("poisoning" in t.lower() for t in titles)
