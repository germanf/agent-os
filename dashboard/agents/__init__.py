from .hermes_agent import HermesAgent
from .opencode_agent import OpencodeAgent, is_server_available, start_server, stop_server
from .protocol import (
    AgentCapability,
    AgentContext,
    AgentResult,
    DeveloperCapability,
    HandoffRequest,
    HandoffResponse,
    HandoffStatus,
    OrchestratorCapability,
    QACapability,
    ReviewerCapability,
    SecurityCapability,
    Severity,
    UIUXCapability,
    validate_handoff,
)
from .reviewer import TechLeadAgent
from .security_agent import SecuritySpecialistAgent
from .uiux_agent import UIUXSpecialistAgent

_registry: dict[str, AgentCapability] = {}


def register_agent(agent: AgentCapability) -> None:
    _registry[agent.name] = agent


def get_agent(name: str) -> AgentCapability | None:
    return _registry.get(name)


def list_agents() -> list[dict]:
    return [
        {
            "name": agent.name,
            "description": agent.description,
            "capability": agent.capability_id(),
        }
        for agent in _registry.values()
    ]


__all__ = [
    "AgentCapability",
    "AgentContext",
    "AgentResult",
    "DeveloperCapability",
    "HandoffRequest",
    "HandoffResponse",
    "HandoffStatus",
    "HermesAgent",
    "OpencodeAgent",
    "OrchestratorCapability",
    "QACapability",
    "ReviewerCapability",
    "SecurityCapability",
    "SecuritySpecialistAgent",
    "Severity",
    "TechLeadAgent",
    "UIUXCapability",
    "UIUXSpecialistAgent",
    "get_agent",
    "is_server_available",
    "list_agents",
    "register_agent",
    "start_server",
    "stop_server",
    "validate_handoff",
]


# ── Auto-register known agents ──────────────────────────────────────────

register_agent(OpencodeAgent())
register_agent(HermesAgent())
register_agent(TechLeadAgent())
register_agent(SecuritySpecialistAgent())
register_agent(UIUXSpecialistAgent())
