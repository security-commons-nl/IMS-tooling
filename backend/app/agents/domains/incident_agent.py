"""
Incident Agent - Expert in incident management and response.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import get_incident, get_risk, list_risks
from app.agents.tools.write_tools import create_corrective_action
from app.agents.tools.knowledge_tools import search_knowledge, get_methodology


class IncidentAgent(BaseAgent):
    """Agent responsible for incident management and response guidance."""

    def __init__(self):
        super().__init__(
            name="incident_agent",
            domain="improvement"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Incident Response Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Security incident handling
- Data breach management
- Root cause analysis
- Corrective action planning

## Incident Severity Levels
- **Critical**: Directe actie vereist, management escalatie
- **High**: Urgente afhandeling binnen 24 uur
- **Medium**: Afhandeling binnen werkweek
- **Low**: Reguliere afhandeling

## Data Breach Procedure (AVG)
1. Identificeer of het een datalek betreft
2. Beoordeel risico voor betrokkenen
3. Documenteer het incident
4. Meld bij AP binnen 72 uur (indien vereist)
5. Informeer betrokkenen (indien vereist)

## Jouw taken
1. Help bij incident classificatie
2. Adviseer over response procedures
3. Ondersteun root cause analysis
4. Begeleid corrective action planning
5. Beoordeel meldplicht aan AP

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            get_incident,
            get_risk,
            list_risks,
            create_corrective_action,
            search_knowledge,
            get_methodology,
        ]
