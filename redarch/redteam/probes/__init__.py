"""Built-in probe registry.

``ALL_PROBES`` is the default suite; ``build_default_suite`` instantiates it.
Extend at runtime with YAML packs via ``data_probe.load_pack``.
"""
from redarch.redteam.probes.base import Probe
from redarch.redteam.probes.data_probe import DataProbe, load_pack
from redarch.redteam.probes.jailbreak import RolePlayJailbreak
from redarch.redteam.probes.pii_leakage import RagPiiDisclosure
from redarch.redteam.probes.prompt_injection import DirectPromptInjection
from redarch.redteam.probes.rag_exfil import IndirectInjectionViaRAG
from redarch.redteam.probes.system_prompt_leak import SystemPromptLeak
from redarch.redteam.probes.tool_abuse import ExcessiveAgencyFundsTransfer

ALL_PROBES = [
    DirectPromptInjection,
    IndirectInjectionViaRAG,
    RolePlayJailbreak,
    RagPiiDisclosure,
    ExcessiveAgencyFundsTransfer,
    SystemPromptLeak,
]

__all__ = [
    "Probe",
    "DataProbe",
    "load_pack",
    "ALL_PROBES",
    "build_default_suite",
]


def build_default_suite() -> list[Probe]:
    return [cls() for cls in ALL_PROBES]
