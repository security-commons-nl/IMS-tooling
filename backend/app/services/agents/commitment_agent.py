"""Commitment agent — Step 1: Bestuurlijk commitment."""

from app.services.agents.base_agent import BaseAgent


class CommitmentAgent(BaseAgent):
    agent_name = "commitment-agent"
    step_number = "1"
    prompt_file = "commitment.txt"

    def get_greeting(self) -> str:
        return (
            "Welkom bij stap 1: Bestuurlijk commitment. "
            "Ik help u bij het opstellen van een besluitmemo voor het bestuur.\n\n"
            "Heeft u al een bestaand besluitmemo of vergelijkbaar document, "
            "of wilt u dat ik u door de vragen leid?"
        )
