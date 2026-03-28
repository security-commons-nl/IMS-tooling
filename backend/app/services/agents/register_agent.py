"""Register agent — Step 5: Registers & risicobeoordeling."""

from app.services.agents.base_agent import BaseAgent


class RegisterAgent(BaseAgent):
    agent_name = "register-agent"
    step_number = "5"
    prompt_file = "register.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 5: Registers & risicobeoordeling. "
            "Ik help u bij het inventariseren van bestaande registers, "
            "het opstellen van een eerste risicobeeld en de risicobeoordelingsmethodiek.\n\n"
            "Heeft u al (gedeeltelijke) registers beschikbaar?"
        )
