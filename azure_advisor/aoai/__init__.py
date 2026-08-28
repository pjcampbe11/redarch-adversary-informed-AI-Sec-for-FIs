"""
aoai/ — Azure OpenAI: the model deployment.

  client.py → the production chat client (keyless), with tool-calling support.
  target.py → the same endpoint wrapped as a red-team TARGET for the harness,
              so you attack the real deployment with the real auth path.

Mental model (Ch. 11): you call a *deployment name* (e.g. "advisor-gpt4o"), not a
model name; the api-version pins the request/response schema. The model is
UNTRUSTED — everything protective lives in safety/, rag/, agent/, identity/.
"""
from azure_advisor.aoai.client import AoaiClient

__all__ = ["AoaiClient"]
