import logging
from typing import Dict, Any, Optional, List
from app.agents.core.base_agent import BaseAgent
from app.agents.core.intent_router import IntentRouter, RoutingDecision
from app.agents.domains import ALL_AGENTS

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Routes interactions to the appropriate agent based on context.

    Supports:
    - Intent-based routing (keyword scoring + LLM fallback)
    - Agent selection by name (manual override)
    - Context-based agent detection (legacy, for /detect endpoint)
    - Agent listing for UI
    """

    # Mapping of page contexts to recommended agents
    CONTEXT_AGENT_MAP = {
        "risk": "risk",
        "risks": "risk",
        "decision": "risk",
        "decisions": "risk",
        "besluit": "risk",
        "besluitlog": "risk",
        "risk-framework": "risk",
        "risicokader": "risk",
        "behandelstrategie": "risk",
        "treatment": "risk",
        "in-control": "risk",
        "in_control": "risk",
        "measure": "measure",
        "measures": "measure",
        "policy": "policy",
        "policies": "policy",
        "policy-principles": "policy",
        "uitgangspunten": "policy",
        "beleid-trace": "policy",
        "principle": "policy",
        "scope": "scope",
        "scopes": "scope",
        "asset": "scope",
        "assets": "scope",
        "assessment": "assessment",
        "assessments": "assessment",
        "audit": "assessment",
        "incident": "incident",
        "incidents": "incident",
        "privacy": "privacy",
        "dpia": "privacy",
        "continuity": "bcm",
        "bcm": "bcm",
        "supplier": "supplier",
        "suppliers": "supplier",
        "improvement": "improvement",
        "corrective": "improvement",
        "act-overdue": "improvement",
        "feedbackloop": "improvement",
        "workflow": "workflow",
        "planning": "planning",
        "report": "report",
        "dashboard": "report",
        "ms-hub": "report",
        "objective": "objectives",
        "kpi": "objectives",
        "maturity": "maturity",
        "admin": "admin",
        "compliance": "compliance",
        "soa": "compliance",
        "backlog": "planning",
        "simulation": "risk",
        "frameworks": "compliance",
        "reports": "report",
        "controls": "compliance",
        "relaties": "report",
        "relationships": "report",
        "users": "admin",
        "organization": "onboarding",
        "onboarding": "onboarding",
        "profiel": "onboarding",
    }

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.intent_router = IntentRouter()
        self._register_all_agents()

    def _register_all_agents(self):
        """Register all available agents."""
        for name, agent_class in ALL_AGENTS.items():
            try:
                self.agents[name] = agent_class()
            except Exception as e:
                print(f"Warning: Failed to initialize {name} agent: {e}")

    def register_agent(self, agent: BaseAgent):
        """Register an initialized agent."""
        self.agents[agent.name] = agent

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[Dict[str, str]]:
        """List all available agents with their info."""
        return [
            {
                "name": agent.name,
                "domain": agent.domain,
                "description": agent.get_system_prompt()[:200] + "..."
            }
            for agent in self.agents.values()
        ]

    def detect_agent_from_context(self, page: str = None, entity_type: str = None) -> str:
        """
        Detect the best agent based on page/entity context.

        Returns agent name or 'risk' as default.
        """
        # Check page context
        if page:
            page_lower = page.lower()
            for key, agent_name in self.CONTEXT_AGENT_MAP.items():
                if key in page_lower:
                    return agent_name

        # Check entity type
        if entity_type:
            entity_lower = entity_type.lower()
            if entity_lower in self.CONTEXT_AGENT_MAP:
                return self.CONTEXT_AGENT_MAP[entity_lower]

        # Default to risk agent
        return "risk"

    async def route_request(
        self,
        message: str,
        context: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Route a message to the best agent using intent-based routing.

        Context can include:
        - agent_name: Explicit agent selection (manual override)
        - page: Current page for context boost
        - entity_type: Current entity type for context boost

        Returns dict with 'response', 'agent_used', 'routing_method'.
        """
        manual_override = context.get("agent_name")

        # Use intent router
        decision: RoutingDecision = await self.intent_router.route(
            message=message,
            page=context.get("page"),
            entity_type=context.get("entity_type"),
            manual_override=manual_override,
        )

        logger.info(
            f"Routing: '{message[:60]}...' → {decision.agent_name} "
            f"(method={decision.method}, confidence={decision.confidence})"
        )

        agent = self.get_agent(decision.agent_name)
        if not agent:
            agent = self.get_agent("risk")
            if not agent:
                return {
                    "response": "Error: No agents available.",
                    "agent_used": "none",
                    "routing_method": "error",
                }

        response_text = await agent.chat(message, context, history)

        return {
            "response": response_text,
            "agent_used": decision.agent_name,
            "routing_method": decision.method,
        }


# Global instance
orchestrator = AgentOrchestrator()
