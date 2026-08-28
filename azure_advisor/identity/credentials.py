"""
credentials.py — password-less service authentication (managed identity).

Field guide: Ch. 04 (keyless AOAI target) and Ch. 14 (Entra ID spine).

WHAT THIS SOLVES
API keys are the #1 thing that leaks — into prompts, configs, logs, and repos.
`DefaultAzureCredential` removes them entirely: in Azure it uses the resource's
managed identity; on a dev box it falls back to your `az login`. Same code,
no secret in either place.

WHY A "TOKEN PROVIDER" FOR AZURE OPENAI
The OpenAI SDK wants a bearer token on every call. `get_bearer_token_provider`
wraps the credential so the SDK can fetch/refresh a token for the Cognitive
Services scope automatically — you never hold the token yourself.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

# Scope that mints tokens valid for Azure OpenAI / Cognitive Services data plane.
COGNITIVE_SCOPE = "https://cognitiveservices.azure.com/.default"


@lru_cache(maxsize=1)
def azure_credential():
    """Return a cached DefaultAzureCredential.

    Lazy import so the package imports even when azure-identity isn't installed
    (e.g. in `--demo` mode). Cached because credential construction probes the
    environment and we want to do that once.
    """
    from azure.identity import DefaultAzureCredential

    # exclude_interactive_browser keeps this non-interactive for services/CI.
    return DefaultAzureCredential(exclude_interactive_browser_credential=True)


def aoai_token_provider() -> Callable[[], str]:
    """Return a callable the OpenAI SDK uses to get/refresh AOAI bearer tokens."""
    from azure.identity import get_bearer_token_provider

    return get_bearer_token_provider(azure_credential(), COGNITIVE_SCOPE)


def managed_identity_client_assertion() -> str:
    """Client assertion (a signed token) proving the app's identity, without a
    client secret. Used by the OBO flow so even user-context exchanges stay
    password-less. In Azure this is backed by the managed identity; here it is a
    thin wrapper you point at your federated-credential setup.
    """
    cred = azure_credential()
    # api://AzureADTokenExchange is the audience Entra expects for a federated
    # client assertion. The returned JWT is the app's proof-of-identity.
    return cred.get_token("api://AzureADTokenExchange/.default").token
