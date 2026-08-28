"""Controls-as-code — guardrails expressed as testable assertions.

The same system spec that feeds the threat model is evaluated against a policy
file. Each control targets components with a selector and asserts a property.
No code is eval'd from policy files; only the declarative selectors/assertions
below are honoured, so a policy is safe to accept from a repo/PR.
"""
from redarch.controls.policy import evaluate_policy, load_policy

__all__ = ["evaluate_policy", "load_policy"]
