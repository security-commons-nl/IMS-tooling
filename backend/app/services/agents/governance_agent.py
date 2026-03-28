"""Governance agent — Step 3a: Governance- en beleidsvoorstel opstellen."""

from app.services.agents.base_agent import BaseAgent


class GovernanceAgent(BaseAgent):
    agent_name = "governance-agent"
    step_number = "3a"
    prompt_file = "governance.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 3a: Governance- en beleidsvoorstel opstellen. "
            "Ik help u bij het uitwerken van de governance-structuur, "
            "het IMS-beleid en de communicatiematrix.\n\n"
            "Heeft u al bestaande governance-documenten of beleidsnotities, "
            "of bouwen we het op basis van de eerdere stappen?"
        )
