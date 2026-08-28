"""
rag/ — retrieval over the participant data (Azure AI Search on Databricks data).

Field guide: Ch. 07 (data governance & exfil) and Ch. 13 (RAG over Databricks).

Three files, three jobs:
  retrieval.py → security-TRIMMED search: only rows the CALLER may see (uses the
                 OBO identity, not the service identity).
  redaction.py → tokenize/redact PII BEFORE it reaches the model context.
  grounding.py → assemble the grounded prompt, SPOTLIGHTING retrieved text so
                 the model treats it as data, never instructions.

The entitlement lives in retrieval.py — in the query filter — never in the prompt.
"""
from azure_advisor.rag.grounding import build_grounded_messages
from azure_advisor.rag.redaction import redact_pii
from azure_advisor.rag.retrieval import retrieve_entitled

__all__ = ["retrieve_entitled", "redact_pii", "build_grounded_messages"]
