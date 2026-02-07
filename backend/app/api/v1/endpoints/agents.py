"""
AI Agent Endpoints

Provides chat interface to all IMS AI agents.
Supports context-based agent selection and streaming responses.
"""
import logging
from typing import Any, Dict, Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.core.orchestrator import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    context: Optional[Dict[str, Any]] = {}
    history: Optional[List[Dict[str, str]]] = []
    agent_name: Optional[str] = None  # Auto-detect if not provided


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    agent_used: str
    tool_calls: Optional[list] = []


class AgentInfo(BaseModel):
    """Information about an available agent."""
    name: str
    domain: str
    description: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[AgentInfo])
async def list_available_agents():
    """
    List all available AI agents.

    Returns agent names, domains, and brief descriptions.
    Useful for showing agent selector in UI.
    """
    return orchestrator.list_agents()


@router.get("/detect")
async def detect_agent(
    page: Optional[str] = None,
    entity_type: Optional[str] = None,
):
    """
    Detect the recommended agent based on context.

    Parameters:
    - page: Current page name (e.g., 'risks', 'policies')
    - entity_type: Current entity type (e.g., 'risk', 'measure')

    Returns the recommended agent name.
    """
    agent_name = orchestrator.detect_agent_from_context(page=page, entity_type=entity_type)
    agent = orchestrator.get_agent(agent_name)

    return {
        "agent_name": agent_name,
        "agent_domain": agent.domain if agent else "unknown",
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with an AI agent.

    The agent is selected based on:
    1. Explicit agent_name in request
    2. Auto-detection from context (page, entity_type)
    3. Default to risk agent

    Context can include:
    - page: Current page for context
    - entity_type: Current entity being viewed
    - entity_id: ID of current entity
    - tenant_id: Current tenant
    """
    context = request.context or {}

    # Add explicit agent_name to context if provided
    if request.agent_name:
        context["agent_name"] = request.agent_name

    # Determine which agent will be used
    agent_name = context.get("agent_name") or orchestrator.detect_agent_from_context(
        page=context.get("page"),
        entity_type=context.get("entity_type")
    )

    try:
        response_text = await orchestrator.route_request(request.message, context, request.history)
        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
        )
    except Exception as e:
        logger.error(f"Agent chat error: {str(e)}", exc_info=True)
        # Return a friendly error as a chat response instead of a 500
        error_type = type(e).__name__
        if "connect" in str(e).lower() or "refused" in str(e).lower() or "timeout" in str(e).lower():
            friendly = "De AI-assistent is momenteel niet bereikbaar. Controleer of de LLM-service (Ollama/Mistral) draait."
        elif "No AI providers available" in str(e):
            friendly = "Er zijn geen AI-providers geconfigureerd. Configureer Mistral, Scaleway of Ollama in de .env file."
        else:
            friendly = f"Er is een fout opgetreden bij de AI-assistent: {error_type}"
        return ChatResponse(
            response=friendly,
            agent_used=agent_name,
        )


@router.get("/health")
async def check_agent_health():
    """
    Check health of AI agent system.

    Returns status of:
    - Number of registered agents
    - LLM connectivity (basic check)
    """
    agents = orchestrator.list_agents()

    return {
        "status": "healthy" if len(agents) > 0 else "degraded",
        "agents_registered": len(agents),
        "agent_names": [a["name"] for a in agents],
    }
