"""
azure_advisor — a secure wealth-management "Advisor Copilot" on Azure.

This package is the Azure code from the field guide *Breaking the Advisor
Copilot*, broken out into one module per moving piece and heavily commented so
each part can be read, tested, and lifted on its own.

The whole point of the design is defense-in-depth around an UNTRUSTED model:

    identity → safety(in) → rag(entitled) → aoai(model) → safety(out) → agent(broker)

Read `docs/ARCHITECTURE.md` for the request trace that ties these together, and
`docs/MODULES.md` for a one-paragraph description of every file.

Nothing here needs the Azure SDKs installed just to import — the SDK imports are
lazy (inside functions), and `pipeline.py --demo` runs the full flow with
in-memory stubs so you can see the moving pieces without a live tenant.
"""
__version__ = "0.1.0"
__all__ = ["config"]
