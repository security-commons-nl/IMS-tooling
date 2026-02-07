"""
Chat State - AI Chat Island state management
"""
from typing import List, Dict, Any, Optional
import reflex as rx
from ims.api.client import api_client


class ChatMessage(rx.Base):
    """A chat message."""
    role: str  # "user" or "assistant"
    content: str
    agent: Optional[str] = None


class ChatState(rx.State):
    """State for AI Chat Island."""

    # Chat state
    messages: List[ChatMessage] = []
    current_input: str = ""
    is_loading: bool = False
    is_open: bool = False
    error: str = ""

    # Agent state
    current_agent: str = "risk"
    available_agents: List[Dict[str, str]] = []

    # Context (set by page)
    page_context: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None

    # Auto-routing: tracks whether user manually picked an agent
    _manual_override: bool = False

    @rx.var
    def has_messages(self) -> bool:
        """Check if there are any messages."""
        return len(self.messages) > 0

    @rx.var
    def agent_display_name(self) -> str:
        """Get display name for current agent."""
        agent_names = {
            "risk": "Risico Expert",
            "measure": "Maatregelen Expert",
            "policy": "Beleid Expert",
            "compliance": "Compliance Expert",
            "assessment": "Assessment Expert",
            "incident": "Incident Expert",
            "privacy": "Privacy Expert",
            "bcm": "Continuïteit Expert",
            "supplier": "Leverancier Expert",
            "improvement": "Verbetering Expert",
            "workflow": "Workflow Expert",
            "planning": "Planning Expert",
            "report": "Rapportage Expert",
            "objectives": "Doelstellingen Expert",
            "maturity": "Maturity Expert",
            "admin": "Admin Expert",
        }
        return agent_names.get(self.current_agent, "AI Assistent")

    def scroll_bottom(self):
        """Scroll chat to bottom with retry logic to ensure render is complete."""
        return rx.call_script(
            """
            var e = document.getElementById('chat-messages-container');
            if(e) {
                e.scrollTop = e.scrollHeight;
                setTimeout(() => e.scrollTop = e.scrollHeight, 100);
                setTimeout(() => e.scrollTop = e.scrollHeight, 300);
            }
            """
        )

    def focus_input(self):
        """Focus the chat input field."""
        return rx.call_script(
            "setTimeout(() => { var e = document.getElementById('chat-input'); if(e) e.focus(); }, 100)"
        )

    def toggle_chat(self):
        """Toggle chat panel open/closed."""
        self.is_open = not self.is_open
        if self.is_open:
            return [self.focus_input(), self.scroll_bottom()]

    def open_chat(self):
        """Open the chat panel."""
        self.is_open = True
        return [self.focus_input(), self.scroll_bottom()]

    def close_chat(self):
        """Close the chat panel."""
        self.is_open = False

    def set_input(self, value: str):
        """Update input field."""
        self.current_input = value

    def set_agent(self, agent_name: str):
        """Manually select an agent (overrides auto-detection)."""
        self.current_agent = agent_name
        self._manual_override = True

    def set_context(self, page: str = "", entity_type: str = "", entity_id: int = None):
        """Set the page context for agent selection."""
        self.page_context = page
        self.entity_type = entity_type
        self.entity_id = entity_id

    async def sync_page_context(self):
        """Auto-detect agent from current page route.

        Called on_mount by layout — reads the router path and triggers
        detect_agent() unless the user manually picked an agent.
        Manual override resets on page navigation.
        """
        page = self.router.page.path.strip("/").split("/")[0] or "dashboard"

        # Only act when the page actually changed
        if page == self.page_context:
            return

        self.page_context = page
        self._manual_override = False  # reset on navigation

        await self.detect_agent()

    def clear_chat(self):
        """Clear all messages."""
        self.messages = []
        self.error = ""

    async def load_agents(self):
        """Load available agents from API."""
        try:
            agents = await api_client.get_agents()
            self.available_agents = agents
        except Exception as e:
            self.error = f"Kon agents niet laden: {str(e)}"

    async def send_message(self):
        """Send a message to the current agent."""
        if not self.current_input.strip():
            return

        # Add user message
        user_msg = ChatMessage(role="user", content=self.current_input)
        self.messages = self.messages + [user_msg]
        
        # Clear input and set loading
        message = self.current_input
        self.current_input = ""
        self.is_loading = True
        self.error = ""
        
        # Yield to update UI and scroll
        yield self.scroll_bottom()

        try:
            # Build context
            context = {
                "page": self.page_context,
                "entity_type": self.entity_type,
            }
            if self.entity_id:
                context["entity_id"] = self.entity_id

            # Prepare history (exclude the just added user message from history to prevent duplication if backend adds it)
            # Actually, standard pattern is to send full history excluding the NEWEST message which is sent as 'message'
            history = [
                {"role": m.role, "content": m.content} 
                for m in self.messages[:-1]
            ]

            # Send to API
            response = await api_client.chat_with_agent(
                message=message,
                agent_name=self.current_agent,
                context=context,
                history=history,
            )

            # Add assistant response
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.get("response", "Geen antwoord ontvangen."),
                agent=response.get("agent_used", self.current_agent),
            )
            self.messages = self.messages + [assistant_msg]

        except Exception as e:
            error_detail = str(e) or "Verbinding verbroken of time-out."
            self.error = f"Fout bij versturen: {error_detail}"
            # Add error message
            error_msg = ChatMessage(
                role="assistant",
                content=f"Er ging iets mis: {error_detail}",
                agent=self.current_agent,
            )
            self.messages = self.messages + [error_msg]

        finally:
            self.is_loading = False
            # Scroll to bottom again after response
            yield self.scroll_bottom()

    async def detect_agent(self):
        """Auto-detect the best agent for current context."""
        try:
            result = await api_client.detect_agent(
                page=self.page_context,
                entity_type=self.entity_type,
            )
            self.current_agent = result.get("agent_name", "risk")
        except Exception:
            # Default to risk agent on error
            self.current_agent = "risk"
