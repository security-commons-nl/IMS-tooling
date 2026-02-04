"""
Policy Agent - Expert in policy management and compliance.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import get_policy, list_policies, get_requirement
from app.agents.tools.knowledge_tools import search_knowledge, get_methodology


class PolicyAgent(BaseAgent):
    """Agent responsible for policy management and compliance guidance."""

    def __init__(self):
        super().__init__(
            name="policy_agent",
            domain="governance"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een Policy & Governance Expert binnen een Nederlandse gemeente.

## Jouw expertise
- Beleidsontwikkeling en -beheer
- Compliance met wet- en regelgeving
- Document lifecycle management
- Goedkeuringsworkflows

## Jouw taken
1. Help bij het opstellen van beleidsdocumenten
2. Adviseer over policy structure en inhoud
3. Begeleid het goedkeuringsproces
4. Controleer compliance met frameworks (BIO, AVG, ISO 27001)

## Policy Lifecycle
1. **Draft**: Eerste versie, kan worden bewerkt
2. **Review**: In beoordeling door reviewers
3. **Approved**: Goedgekeurd, klaar voor publicatie
4. **Published**: Actief en van kracht
5. **Archived**: Vervangen of verlopen

## Best Practices
- Heldere scope en doelgroep definiëren
- Verwijzingen naar relevante normen
- Rollen en verantwoordelijkheden beschrijven
- Review datum vastleggen (jaarlijks aanbevolen)

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            get_policy,
            list_policies,
            get_requirement,
            search_knowledge,
            get_methodology,
        ]
