"""
External Integrations Module

Provides clients for connecting to external platforms:
- TopDesk: ITSM, assets, incidents
- ServiceNow: ITSM, CMDB
- Proquro: Supplier/vendor management
- BlueDolphin: Enterprise architecture, applications
"""

from app.integrations.base import BaseIntegration, IntegrationConfig
from app.integrations.topdesk import TopDeskClient
from app.integrations.servicenow import ServiceNowClient
from app.integrations.proquro import ProquroClient
from app.integrations.bluedolphin import BlueDolphinClient

__all__ = [
    "BaseIntegration",
    "IntegrationConfig",
    "TopDeskClient",
    "ServiceNowClient",
    "ProquroClient",
    "BlueDolphinClient",
]
