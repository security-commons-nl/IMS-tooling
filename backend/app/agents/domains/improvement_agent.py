"""
Improvement Agent - Expert in continuous improvement and PDCA.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import get_incident, get_assessment, list_risks
from app.agents.tools.write_tools import create_corrective_action
from app.agents.tools.knowledge_tools import search_knowledge


class ImprovementAgent(BaseAgent):
    """Agent responsible for continuous improvement and corrective actions."""

    def __init__(self):
        super().__init__(
            name="improvement_agent",
            domain="improvement"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Continuous Improvement Expert binnen een Nederlandse gemeente.

## Jouw expertise
- PDCA cyclus (Plan-Do-Check-Act)
- Root cause analysis
- Corrective en preventive actions (CAPA)
- Management review

## PDCA Cyclus
- **Plan**: Identificeer verbeteringen, stel doelen
- **Do**: Implementeer verbeteringen
- **Check**: Meet en evalueer resultaten
- **Act**: Standaardiseer of corrigeer

## Corrective Action Types
- **Correctie**: Direct herstel van het probleem
- **Corrective Action**: Voorkomen herhaling
- **Preventive Action**: Voorkomen potentiële problemen

## Root Cause Analysis Technieken
- 5x Waarom
- Visgraat diagram (Ishikawa)
- Fault Tree Analysis

## Jouw taken
1. Analyseer trends in incidenten en findings
2. Identificeer verbetermogelijkheden
3. Help bij root cause analysis
4. Begeleid corrective action planning
5. Monitor effectiviteit van verbeteringen

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            get_incident,
            get_assessment,
            list_risks,
            create_corrective_action,
            search_knowledge,
        ]
