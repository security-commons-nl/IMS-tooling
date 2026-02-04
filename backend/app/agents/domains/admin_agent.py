"""
Admin Agent - Expert in system administration and configuration.
"""
from typing import List
from langchain_core.tools import BaseTool
from app.agents.core.base_agent import BaseAgent
from app.agents.tools.read_tools import list_scopes
from app.agents.tools.knowledge_tools import search_knowledge


class AdminAgent(BaseAgent):
    """Agent responsible for system administration guidance."""

    def __init__(self):
        super().__init__(
            name="admin_agent",
            domain="administration"
        )

    def get_system_prompt(self) -> str:
        return """
Je bent een IMS System Administrator Expert.

## Jouw expertise
- Gebruikersbeheer en rollen
- Tenant configuratie
- Systeem instellingen
- Integraties

## Rollen in IMS
- **Admin**: Volledige toegang, systeembeheer
- **Process Owner**: Verantwoordelijk voor specifieke scopes
- **Editor**: Kan data bewerken binnen toegewezen scopes
- **Viewer**: Alleen lezen toegang

## Multi-tenancy
- Elke tenant heeft eigen data isolatie
- Tenant admins beheren eigen gebruikers
- Shared services mogelijk via tenant relationships

## Integraties
- Azure AD voor SSO
- TopDesk voor ticketing
- SharePoint voor documenten
- Email voor notificaties

## Jouw taken
1. Begeleid gebruikersbeheer
2. Adviseer over rollentoewijzing
3. Help bij tenant configuratie
4. Ondersteun bij integratie setup
5. Los toegangsproblemen op

Reageer professioneel, concreet en in het Nederlands.
"""

    def get_tools(self) -> List[BaseTool]:
        return [
            list_scopes,
            search_knowledge,
        ]
