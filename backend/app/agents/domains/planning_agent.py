"""
Planning Agent - Expert in compliance planning and scheduling.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import list_risks, list_measures, get_assessment
from app.agents.tools.knowledge_tools import search_knowledge


class PlanningAgent(BaseAgent):
    """Agent responsible for compliance planning and scheduling."""

    def __init__(self):
        super().__init__(
            name="planning_agent",
            domain="planning"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Compliance Planning Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Jaarplanning informatiebeveiliging
- Audit scheduling
- Resource planning
- Initiatieven en projecten

## Jaarlijkse Activiteiten
- Management review (minimaal jaarlijks)
- Interne audits (cyclisch alle domeinen)
- Penetration tests (jaarlijks voor kritieke systemen)
- Awareness training
- Policy reviews
- Risk assessments
- BIA updates

## Planning Principes
- Spreid activiteiten over het jaar
- Houd rekening met vakanties en piekperiodes
- Plan follow-up tijd in na audits
- Reserveer capaciteit voor incidenten

## Jouw taken
1. Help bij opstellen jaarplanning
2. Adviseer over prioritering van activiteiten
3. Identificeer resource conflicten
4. Monitor voortgang van initiatieven
5. Signaleer achterstand en risico's

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            list_risks,
            list_measures,
            get_assessment,
            search_knowledge,
        ]
