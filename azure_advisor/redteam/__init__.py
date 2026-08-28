"""
redteam/ — point the multi-agent harness at the Azure OpenAI target.

Field guide: Ch. 03/04. This wraps pjcampbe11/multi-agent-harness so the
Attacker/Verifier/Optimizer loop runs against the REAL deployment via aoai/target.
Authorized use only; supply your own objectives from public benchmarks.
"""
from azure_advisor.redteam.campaign import (
    AzureOpenAILLMClient,
    load_objectives,
    run_campaign,
)

__all__ = ["run_campaign", "AzureOpenAILLMClient", "load_objectives"]
