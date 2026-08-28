"""
config.py — one place for every endpoint, deployment name, and policy knob.

Why this exists: the field guide's snippets each hard-coded their own endpoint or
deployment string. In a real system those belong in one typed settings object,
sourced from environment variables (or Key Vault references), never from code and
never from a prompt. Copy `.env.example` to `.env` and fill it in.

Nothing secret lives here — only *names* and *policy*. Secrets (if any) are pulled
at runtime from managed identity or Key Vault; see identity/credentials.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AzureSettings:
    # --- Azure OpenAI (the model deployment; see aoai/) ---------------------
    aoai_endpoint: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    aoai_deployment: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "advisor-gpt4o")
    aoai_api_version: str = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")

    # --- Azure AI Search (the RAG index over Databricks data; see rag/) ------
    search_endpoint: str = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
    search_index: str = os.environ.get("AZURE_SEARCH_INDEX", "participants")

    # --- Azure AI Content Safety (the input/output firewall; see safety/) ----
    content_safety_endpoint: str = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT", "")

    # --- Entra ID (the identity spine; see identity/) ------------------------
    tenant_id: str = os.environ.get("AZURE_TENANT_ID", "")
    client_id: str = os.environ.get("AZURE_CLIENT_ID", "")
    rag_api_scope: str = os.environ.get("RAG_API_SCOPE", "api://voya-rag/.default")

    # --- Action-broker policy (see agent/broker.py) --------------------------
    # Money movement above this auto-limit, or to any external destination,
    # forces a human approval + step-up auth. These are POLICY, enforced
    # outside the model — the model can never override them.
    transfer_auto_limit_usd: float = float(os.environ.get("TRANSFER_AUTO_LIMIT_USD", "0"))
    external_transfer_needs_approval: bool = True

    def missing(self) -> list[str]:
        """Return the names of unset-but-required settings (for --demo checks)."""
        required = {
            "AZURE_OPENAI_ENDPOINT": self.aoai_endpoint,
            "AZURE_SEARCH_ENDPOINT": self.search_endpoint,
            "AZURE_CONTENT_SAFETY_ENDPOINT": self.content_safety_endpoint,
            "AZURE_TENANT_ID": self.tenant_id,
            "AZURE_CLIENT_ID": self.client_id,
        }
        return [k for k, v in required.items() if not v]


# Import this singleton everywhere: `from azure_advisor.config import SETTINGS`
SETTINGS = AzureSettings()
