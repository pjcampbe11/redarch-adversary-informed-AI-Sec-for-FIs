"""
identity/ — the spine. Every other module authenticates through here.

Two distinct jobs live in this package, and confusing them is the classic
"confused deputy" bug (field guide Ch. 09/14):

  credentials.py  → how the SERVICE authenticates to Azure resources it owns
                    (Azure OpenAI, Search, Content Safety). Uses a managed
                    identity: password-less, nothing to leak.

  obo.py          → how the service acts AS THE CALLING USER for data access,
                    so downstream authorization is evaluated with the USER's
                    permissions, not the service's god-mode.

Rule of thumb: talking to a resource the app owns → credentials.py.
Reaching data a specific user is (or isn't) entitled to → obo.py.
"""
from azure_advisor.identity.credentials import aoai_token_provider, azure_credential
from azure_advisor.identity.obo import exchange_on_behalf_of

__all__ = ["azure_credential", "aoai_token_provider", "exchange_on_behalf_of"]
