"""Controls agent — Step 6: Normenkader & kerncontrols."""

from app.services.agents.base_agent import BaseAgent


class ControlsAgent(BaseAgent):
    agent_name = "controls-agent"
    step_number = "6"
    prompt_file = "controls.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 6: Normenkader & kerncontrols. "
            "Ik help u bij het vaststellen van het normenkader en "
            "het selecteren van de minimale werkset kerncontrols.\n\n"
            "Heeft u al een normenkaderdocument of control-overzicht?"
        )
