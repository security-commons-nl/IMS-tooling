"""Context agent — Step 2a: Organisatiecontext vaststellen."""

from app.services.agents.base_agent import BaseAgent


class ContextAgent(BaseAgent):
    agent_name = "context-agent"
    step_number = "2a"
    prompt_file = "context.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 2a: Organisatiecontext vaststellen. "
            "Ik help u bij het in kaart brengen van uw organisatiecontext "
            "conform ISO 27001 4.1 en 4.2.\n\n"
            "Heeft u al een bestaand organisatiecontextdocument of stakeholderregister, "
            "of beginnen we vanaf nul?"
        )
