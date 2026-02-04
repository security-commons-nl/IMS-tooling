from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import BaseTool

from app.services.ai_gateway import ai_gateway

class BaseAgent(ABC):
    """
    Abstract base class for all IMS AI Agents.
    Uses AI Gateway for multi-provider support (Mistral/Scaleway/Ollama).
    """
    
    def __init__(self, name: str, domain: str, model: str = None):
        self.name = name
        self.domain = domain
        # Model selection is now handled by the gateway primarily, 
        # but we keep the field for logging/context if needed.
        self.model = model 
        
        self.system_prompt = self.get_system_prompt()
        self.tools = self.get_tools()
        
        # Get configured runnable from gateway
        self.runnable = ai_gateway.get_runnable(self.tools)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Return list of tools available to this agent."""
        pass
        
    async def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Send a message to the agent and get a response.
        Context can be used to inject dynamic information into the prompt if needed.
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message)
        ]
        
        # In a real implementation, we would handle tool calling loops here.
        # For now, we just invoke the LLM.
        response = await self.runnable.ainvoke(messages)
        return response.content
