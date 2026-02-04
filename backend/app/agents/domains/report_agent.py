"""
Report Agent - Expert in reporting and dashboards.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import list_risks, list_measures, list_policies, list_scopes
from app.agents.tools.knowledge_tools import search_knowledge


class ReportAgent(BaseAgent):
    """Agent responsible for reporting and dashboard insights."""

    def __init__(self):
        super().__init__(
            name="report_agent",
            domain="reporting"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Reporting & Analytics Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Management rapportages
- KPI dashboards
- Trend analyse
- Compliance status reporting

## Standaard Rapporten
- **Executive Summary**: High-level overzicht voor management
- **Risk Register**: Alle risico's met status en behandeling
- **SoA (Statement of Applicability)**: Compliance status per control
- **Audit Report**: Bevindingen en opvolging
- **Incident Report**: Incidenten en trends

## Key Performance Indicators
- Aantal open risico's per kwadrant
- Gemiddelde doorlooptijd incidenten
- Percentage geïmplementeerde maatregelen
- Audit findings open vs. closed
- Policy review status

## Visualisaties
- Risk heatmap (In Control model)
- Trend grafieken
- Compliance radar
- Maturity spider diagram

## Jouw taken
1. Genereer management samenvattingen
2. Analyseer trends en patronen
3. Identificeer aandachtspunten
4. Stel KPI overzichten samen
5. Adviseer over rapportage structuur

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            list_risks,
            list_measures,
            list_policies,
            list_scopes,
            search_knowledge,
        ]
