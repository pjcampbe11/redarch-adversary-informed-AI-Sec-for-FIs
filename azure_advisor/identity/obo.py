"""
obo.py — On-Behalf-Of token exchange (the fix for the confused deputy).

Field guide: Ch. 09 (identity bypass) and Ch. 14 (Entra ID).

THE PROBLEM IT SOLVES (confused deputy, in one breath)
The copilot backend can read ALL participant data — that's its job. If it queries
the data store as ITSELF when you ask a question, it will happily hand you anyone's
record. OBO makes the backend act AS YOU: it swaps your token for a new token that
says "the copilot, for THIS user, with THIS user's permissions only." Every
downstream call then gets authorized as you, so the data layer's own entitlement
checks do the work — no prompt can talk its way past them.

THE FLOW
  1. User signs in to the copilot app  → app receives the user's access token.
  2. Backend calls acquire_token_on_behalf_of(user_token, scopes=[RAG API]).
  3. Entra returns a NEW token scoped to the RAG API, carrying the user's identity.
  4. rag/ uses that token → Azure AI Search sees the user, trims to their rows.

Break any step and you've broken every downstream entitlement at once, which is
why this is a crown-jewel control, not a footnote.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from azure_advisor.config import SETTINGS
from azure_advisor.identity.credentials import managed_identity_client_assertion


@lru_cache(maxsize=1)
def _confidential_app():
    """Build (once) the MSAL confidential client for this app registration.

    Note the credential is a *client assertion* from the managed identity, not a
    client secret — keyless all the way down (see credentials.py).
    """
    import msal

    authority = f"https://login.microsoftonline.com/{SETTINGS.tenant_id}"
    return msal.ConfidentialClientApplication(
        client_id=SETTINGS.client_id,
        authority=authority,
        client_credential={"client_assertion": managed_identity_client_assertion()},
    )


def exchange_on_behalf_of(user_access_token: str,
                          scopes: Optional[list[str]] = None) -> str:
    """Exchange the caller's token for a downstream token scoped to `scopes`,
    carrying the CALLER's identity.

    Args:
        user_access_token: the token the copilot received from the signed-in user.
        scopes: downstream API scopes (defaults to the RAG API from config).

    Returns:
        A downstream access token to attach to rag/ and agent/ calls.

    Raises:
        RuntimeError with the Entra error description if the exchange fails —
        fail closed: no token, no data.
    """
    app = _confidential_app()
    result = app.acquire_token_on_behalf_of(
        user_assertion=user_access_token,
        scopes=scopes or [SETTINGS.rag_api_scope],
    )
    if "access_token" not in result:
        # Surfacing the real reason (consent, audience mismatch, expiry) saves
        # hours; never swallow this and fall back to the service identity.
        raise RuntimeError(f"OBO exchange failed: {result.get('error_description', result)}")
    return result["access_token"]
