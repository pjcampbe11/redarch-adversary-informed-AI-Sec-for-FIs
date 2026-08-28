"""
retrieval.py — security-trimmed retrieval from Azure AI Search.

Field guide: Ch. 07 (the crown-jewel data control).

THE ONE IDEA
The entitlement check happens in the SEARCH FILTER, built from the CALLER's Entra
group membership (delivered via the OBO token), before any result reaches the
model. The model can ask for "Rivera's SSN" all day; if the caller's groups don't
intersect that row's ACL, the row is never retrieved. Authorization by data, not
by prompt.

WHY BOTH TEXT AND VECTOR MUST BE TRIMMED
A vector/similarity query can surface a neighbor's content even when the source
doc was ACL'd, unless the SAME filter is applied to the vector search (Ch. 07
"embedding leak" gotcha, OWASP LLM08). We apply `filter=acl` to both.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from azure_advisor.config import SETTINGS


@dataclass
class RetrievedDoc:
    content: str
    source: str = ""
    score: float = 0.0


def _acl_filter(caller_group_ids: list[str]) -> str:
    """Build an OData filter that keeps only docs whose group_ids intersect the
    caller's groups. Groups come from the OBO'd user token — NOT from anything
    the model said. If the caller has no groups, this yields a filter that
    matches nothing (fail closed)."""
    if not caller_group_ids:
        return "group_ids/any(g: false)"  # matches nothing
    clauses = [f"group_ids/any(g: g eq '{gid}')" for gid in caller_group_ids]
    return " or ".join(clauses)


def _search_client():
    from azure.search.documents import SearchClient
    from azure_advisor.identity.credentials import azure_credential

    return SearchClient(
        endpoint=SETTINGS.search_endpoint,
        index_name=SETTINGS.search_index,
        credential=azure_credential(),
    )


def retrieve_entitled(query: str, caller_group_ids: list[str],
                      top: int = 5) -> list[RetrievedDoc]:
    """Retrieve up to `top` chunks the caller is entitled to.

    Args:
        query: the user's natural-language question.
        caller_group_ids: the CALLER's Entra group object-ids (from OBO).
        top: max results.

    Returns:
        A list of RetrievedDoc — already entitlement-filtered. PII redaction is
        applied by the caller (pipeline) via rag.redact_pii before grounding.
    """
    acl = _acl_filter(caller_group_ids)
    client = _search_client()
    # Hybrid semantic search, trimmed by the ACL filter on BOTH lexical and
    # vector paths (the SDK applies `filter` to the whole query).
    results = client.search(
        search_text=query,
        filter=acl,                       # ← entitlement lives here
        query_type="semantic",
        top=top,
    )
    return [
        RetrievedDoc(
            content=r.get("content", ""),
            source=r.get("source", ""),
            score=r.get("@search.score", 0.0),
        )
        for r in results
    ]
