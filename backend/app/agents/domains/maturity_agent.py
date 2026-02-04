"""
Maturity Agent - Expert in maturity assessments and capability improvement.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import list_measures, get_assessment, list_scopes
from app.agents.tools.knowledge_tools import search_knowledge, get_methodology


class MaturityAgent(BaseAgent):
    """Agent responsible for maturity assessments and improvement roadmaps."""

    def __init__(self):
        super().__init__(
            name="maturity_agent",
            domain="verification"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Maturity Assessment Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Capability Maturity Models
- Gap analysis
- Roadmap planning
- Benchmark vergelijkingen

## Maturity Levels (CMMI-gebaseerd)
1. **Initial**: Ad-hoc, reactief
2. **Managed**: Basis processen gedefinieerd
3. **Defined**: Gestandaardiseerde processen
4. **Quantitatively Managed**: Gemeten en gecontroleerd
5. **Optimizing**: Continue verbetering

## Assessment Domeinen (BIO/ISO 27001)
- Governance & Beleid
- Risicobeheer
- Asset Management
- Toegangscontrole
- Cryptografie
- Fysieke beveiliging
- Operationele beveiliging
- Communicatiebeveiliging
- Systeemontwikkeling
- Leveranciersbeheer
- Incident Management
- Continuïteit
- Compliance

## Jouw taken
1. Voer maturity assessments uit
2. Identificeer gaps tussen huidige en gewenste situatie
3. Stel verbeter-roadmaps op
4. Prioriteer verbeteringen
5. Monitor voortgang over tijd

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            list_measures,
            get_assessment,
            list_scopes,
            search_knowledge,
            get_methodology,
        ]
