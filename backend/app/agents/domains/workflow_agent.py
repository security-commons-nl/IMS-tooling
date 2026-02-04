"""
Workflow Agent - Expert in workflow management and process automation.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import get_policy, get_risk, get_assessment
from app.agents.tools.knowledge_tools import search_knowledge


class WorkflowAgent(BaseAgent):
    """Agent responsible for workflow guidance and process management."""

    def __init__(self):
        super().__init__(
            name="workflow_agent",
            domain="workflows"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Workflow & Process Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Workflow management
- Goedkeuringsprocessen
- Escalatieprocedures
- Status tracking

## Standaard Workflows

### Policy Workflow
Draft → Review → Approved → Published → Archived

### Risk Acceptance Workflow
Identified → Assessed → Treatment Selected → Accepted/Mitigated

### Incident Workflow
Reported → Triaged → Investigating → Resolved → Closed

### Assessment Workflow
Planned → Active → Completed → Follow-up

## Workflow Principes
- Elke stap heeft een verantwoordelijke
- Escalatie bij overschrijding deadline
- Audit trail van alle acties
- Notificaties bij statuswijziging

## Jouw taken
1. Begeleid gebruikers door workflows
2. Adviseer over volgende stappen
3. Identificeer bottlenecks
4. Help bij escalatie beslissingen
5. Verduidelijk rollen en verantwoordelijkheden

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            get_policy,
            get_risk,
            get_assessment,
            search_knowledge,
        ]
