"""Gap agent — Step 4: Gap-analyse."""

from app.services.agents.base_agent import BaseAgent


class GapAgent(BaseAgent):
    agent_name = "gap-agent"
    step_number = "4"
    prompt_file = "gap.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 4: Gap-analyse. "
            "Ik help u bij het uitvoeren van een nulmeting per domein "
            "ten opzichte van het normenkader.\n\n"
            "Heeft u al bestaande risicoanalyses of auditrapportages "
            "die we als input kunnen gebruiken?"
        )
