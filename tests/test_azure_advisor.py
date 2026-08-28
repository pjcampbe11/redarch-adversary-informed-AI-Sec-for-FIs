"""Assert that each demo scenario fires the correct control, plus unit tests for
the individual Azure-code building blocks. No Azure SDKs required."""
from azure_advisor.agent.broker import ActionBroker, Decision
from azure_advisor.pipeline import build_demo_pipeline
from azure_advisor.rag.redaction import redact_pii
from azure_advisor.rag.retrieval import _acl_filter
from azure_advisor.safety.content_safety import dlp_scan


def _step(resp, name_contains):
    return next(s for s in resp.trace if name_contains in s.name)


# --- the four scenarios: each must fire ONE specific control -----------------

def test_entitled_query_answers_and_leaks_nothing():
    p = build_demo_pipeline()
    r = p.handle("advisorA", "How is my client's account doing?")
    assert not r.blocked
    assert _step(r, "retrieve").outcome.startswith("1 doc")
    # PII never appears in the answer even for an entitled caller
    assert dlp_scan(r.answer).blocked is False
    assert "good standing" in r.answer


def test_unentitled_caller_retrieves_nothing():
    p = build_demo_pipeline()
    r = p.handle("advisorB", "What is the balance for Rivera?")
    assert not r.blocked
    assert _step(r, "retrieve").outcome.startswith("0 doc")   # entitlement filter
    assert "don't have access" in r.answer
    assert dlp_scan(r.answer).blocked is False


def test_poisoned_document_blocked_at_input_firewall():
    p = build_demo_pipeline()
    r = p.handle("advisorA", "Summarize this poison uploaded doc")
    assert r.blocked
    fw = _step(r, "input firewall")
    assert fw.blocked and "indirect injection" in fw.outcome
    # blocked BEFORE the model is called
    assert not any(s.name.startswith("model") for s in r.trace)


def test_transfer_request_routed_to_broker_for_approval():
    p = build_demo_pipeline()
    r = p.handle("advisorA", "transfer funds to close the pending item")
    assert not r.blocked                      # answer returns; action does not execute
    assert len(r.tool_outcomes) == 1
    out = r.tool_outcomes[0]
    assert out.tool == "transfer_funds"
    assert out.decision == Decision.NEEDS_APPROVAL


# --- unit tests on the building blocks ---------------------------------------

def test_broker_denies_out_of_scope_tool():
    # advisorB holds only get_balance scope; transfer must be denied outright.
    b = ActionBroker("advisorB", {"tool:get_balance"})
    out = b.handle("transfer_funds", {"amount_usd": 10, "source": "a", "destination": "b"})
    assert out.decision == Decision.DENIED


def test_broker_executes_in_scope_read():
    b = ActionBroker("advisorA", {"tool:get_balance"})
    out = b.handle("get_balance", {"account": "401k-88213"})
    assert out.decision == Decision.EXECUTED


def test_broker_denies_unknown_tool():
    b = ActionBroker("advisorA", {"tool:get_balance", "tool:transfer_funds"})
    assert b.handle("delete_everything", {}).decision == Decision.DENIED


def test_redaction_masks_ssn_to_last4():
    out = redact_pii("SSN 512-88-4417 on file")
    assert "512-88" not in out and "4417" in out


def test_dlp_catches_ssn():
    assert dlp_scan("here is 512-88-4417").blocked is True


def test_acl_filter_empty_groups_matches_nothing():
    # Fail closed: a caller with no groups can retrieve nothing.
    assert _acl_filter([]) == "group_ids/any(g: false)"


def test_acl_filter_builds_or_of_groups():
    f = _acl_filter(["g1", "g2"])
    assert "g1" in f and "g2" in f and " or " in f


# --- red-team campaign wiring (no live harness / Azure needed) ---------------
import pytest
from types import SimpleNamespace
from azure_advisor.redteam.campaign import (
    AzureOpenAILLMClient,
    load_objectives,
    run_campaign,
)


def test_campaign_requires_authorization():
    with pytest.raises(PermissionError):
        run_campaign("nope.jsonl", authorized=False)


def test_campaign_rejects_verifier_equal_target():
    # Guard fires before the harness is imported, so no xteaming needed.
    with pytest.raises(ValueError):
        run_campaign("x.jsonl", authorized=True,
                     target_deployment="advisor-gpt4o", verifier_model="advisor-gpt4o")


def test_objectives_loader_parses_jsonl(tmp_path):
    class FakeObjective:
        def __init__(self, id=None, text="", category=""):
            self.id, self.text, self.category = id, text, category

    f = tmp_path / "obj.jsonl"
    f.write_text('# comment\n{"text":"a","category":"c1"}\n\n{"text":"b"}\n')
    objs = load_objectives(str(f), FakeObjective)
    assert [o.text for o in objs] == ["a", "b"]
    assert objs[0].category == "c1"


def test_azure_target_adapter_routes_to_client():
    # Inject a fake AoaiClient so no Azure/SDK is touched.
    fake = SimpleNamespace(chat=lambda messages, temperature=0.7: SimpleNamespace(text="hi"))
    t = AzureOpenAILLMClient(deployment="advisor-gpt4o", client=fake)
    assert t.chat([{"role": "user", "content": "yo"}]) == "hi"
    assert t.model == "azure:advisor-gpt4o"


def test_azure_target_adapter_labels_platform_block():
    def boom(messages, temperature=0.7):
        raise RuntimeError("The response was filtered: content_filter policy triggered")
    t = AzureOpenAILLMClient(deployment="advisor-gpt4o",
                             client=SimpleNamespace(chat=boom))
    assert t.chat([{"role": "user", "content": "x"}]).startswith("[platform_block]")
