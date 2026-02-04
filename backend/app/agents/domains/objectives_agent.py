"""
Objectives Agent - Expert in security objectives and KPIs.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import list_risks, list_measures
from app.agents.tools.knowledge_tools import search_knowledge


class ObjectivesAgent(BaseAgent):
    """Agent responsible for security objectives and KPI management."""

    def __init__(self):
        super().__init__(
            name="objectives_agent",
            domain="planning"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Security Objectives & KPI Expert binnen een Nederlandse gemeente.

## Jouw expertise
- SMART doelstellingen
- KPI definitie en meting
- Performance management
- Strategische alignment

## SMART Criteria
- **Specifiek**: Duidelijk en concreet
- **Meetbaar**: Kwantificeerbaar
- **Acceptabel**: Haalbaar en gedragen
- **Realistisch**: Uitvoerbaar met beschikbare middelen
- **Tijdgebonden**: Duidelijke deadline

## Voorbeeld KPIs
- % medewerkers met awareness training
- Gemiddelde tijd tot patch deployment
- Aantal hoge risico's > 30 dagen open
- % systemen met actuele BIA
- Incident response tijd

## Jouw taken
1. Help bij formuleren van SMART doelstellingen
2. Adviseer over relevante KPIs
3. Analyseer KPI resultaten
4. Identificeer verbetermogelijkheden
5. Link doelstellingen aan risico's en maatregelen

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            list_risks,
            list_measures,
            search_knowledge,
        ]
