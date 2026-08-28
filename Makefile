.PHONY: install test redteam threatmodel controls assess demo advisor-demo advisor-campaign advisor-campaign-smoke clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

redteam:
	python -m redarch.cli redteam --target examples/targets/mock.yaml --pack examples/probes/finance_pack.yaml

threatmodel:
	python -m redarch.cli threatmodel --spec examples/voya_wealth_advisor.yaml

controls:
	python -m redarch.cli controls --spec examples/voya_wealth_advisor.yaml --policy policies/finserv-genai.yaml

assess:
	python -m redarch.cli assess \
		--spec examples/voya_wealth_advisor.yaml \
		--policy policies/finserv-genai.yaml \
		--target examples/targets/mock.yaml \
		--out reports

demo: assess

# The azure_advisor reference implementation — runs the secure request pipeline
# through four scenarios with in-memory stubs (no Azure, no keys).
advisor-demo:
	python -m azure_advisor.pipeline --demo

# Run the REAL multi-agent (X-Teaming) campaign against the Azure OpenAI target.
# Needs: the xteaming harness on the path (XTEAMING_PATH=... or pip install -e),
# an authorized target, and API keys for the attacker/verifier models.
# Override any variable inline, e.g.:
#   make advisor-campaign OBJECTIVES=bench/my.jsonl TARGET=advisor-gpt4o VERIFIER=gpt-4o MAX_PLANS=1
OBJECTIVES ?= examples/advisor_scope.jsonl
TARGET     ?= advisor-gpt4o
ATTACKER   ?= gpt-4o-mini
VERIFIER   ?= gpt-4o
N_PLANS    ?= 20
MAX_PLANS  ?= 5
OUT        ?= runs
advisor-campaign:
	python -m azure_advisor.redteam.campaign \
		--objectives $(OBJECTIVES) \
		--target-deployment $(TARGET) \
		--attacker $(ATTACKER) --verifier $(VERIFIER) \
		--n-plans $(N_PLANS) --max-plans $(MAX_PLANS) \
		--out $(OUT) \
		--authorized

# Smoke test: the smallest possible real run (1 plan, 1 max-plan) to confirm the
# harness handshake before scaling up. Same requirements as advisor-campaign.
advisor-campaign-smoke:
	python -m azure_advisor.redteam.campaign \
		--objectives $(OBJECTIVES) --target-deployment $(TARGET) \
		--attacker $(ATTACKER) --verifier $(VERIFIER) \
		--n-plans 1 --max-plans 1 --out runs-smoke --authorized

clean:
	rm -rf reports runs runs-smoke .pytest_cache **/__pycache__ *.egg-info
