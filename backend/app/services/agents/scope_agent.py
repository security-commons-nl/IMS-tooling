"""Scope agent — Step 2b: Scope bepalen."""

from app.services.agents.base_agent import BaseAgent


class ScopeAgent(BaseAgent):
    agent_name = "scope-agent"
    step_number = "2b"
    prompt_file = "scope.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 2b: Scope bepalen. "
            "Op basis van de organisatiecontext uit stap 2a help ik u "
            "bij het opstellen van een formeel scopebesluit.\n\n"
            "Heeft u al een scopedocument, of stellen we het samen op?"
        )
