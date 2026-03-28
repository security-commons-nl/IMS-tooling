"""Agent registry — maps step numbers to agent classes."""

from app.services.agents.base_agent import BaseAgent
from app.services.agents.commitment_agent import CommitmentAgent
from app.services.agents.context_agent import ContextAgent
from app.services.agents.scope_agent import ScopeAgent
from app.services.agents.governance_agent import GovernanceAgent
from app.services.agents.gap_agent import GapAgent
from app.services.agents.register_agent import RegisterAgent
from app.services.agents.controls_agent import ControlsAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "1": CommitmentAgent,
    "2a": ContextAgent,
    "2b": ScopeAgent,
    "3a": GovernanceAgent,
    "4": GapAgent,
    "5": RegisterAgent,
    "6": ControlsAgent,
}

# Also index by agent name
AGENT_BY_NAME: dict[str, type[BaseAgent]] = {
    cls.agent_name: cls for cls in AGENT_REGISTRY.values()
}


def get_agent_for_step(step_number: str) -> BaseAgent | None:
    """Get an agent instance for a step number."""
    cls = AGENT_REGISTRY.get(step_number)
    if cls is None:
        return None
    return cls()


def get_agent_by_name(agent_name: str) -> BaseAgent | None:
    """Get an agent instance by its name."""
    cls = AGENT_BY_NAME.get(agent_name)
    if cls is None:
        return None
    return cls()
