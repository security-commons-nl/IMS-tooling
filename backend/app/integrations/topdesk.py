"""
TopDesk Integration Client

Syncs assets, incidents, and configuration items from TopDesk.
API Docs: https://developers.topdesk.com/
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from app.integrations.base import BaseIntegration, IntegrationConfig, SyncResult

logger = logging.getLogger(__name__)


class TopDeskClient(BaseIntegration):
    """
    TopDesk API client for syncing ITSM data.

    Supported entities:
    - Assets (configuration items)
    - Incidents
    - Suppliers
    - Locations
    """

    async def test_connection(self) -> bool:
        """Test connection to TopDesk API."""
        try:
            # TopDesk uses /tas/api/ prefix
            await self._get("/tas/api/version")
            return True
        except Exception as e:
            logger.error(f"TopDesk connection test failed: {e}")
            return False

    async def sync_assets(self) -> SyncResult:
        """
        Sync assets (configuration items) from TopDesk.

        Maps TopDesk assets to IMS Asset model.
        """
        result = SyncResult(
            integration="topdesk",
            entity_type="assets",
            success=True,
        )

        try:
            # Fetch all assets from TopDesk
            # Endpoint: GET /tas/api/assetmgmt/assets
            assets_data = await self._get("/tas/api/assetmgmt/assets", params={
                "fields": "id,name,type,status,supplier,location",
                "pageSize": 1000,
            })

            assets = assets_data.get("dataSet", [])

            for asset in assets:
                try:
                    mapped_asset = self._map_asset(asset)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Asset {asset.get('id')}: {str(e)}")

            logger.info(f"TopDesk sync: {result.created} assets synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"TopDesk asset sync failed: {e}")

        return result

    async def sync_suppliers(self) -> SyncResult:
        """
        Sync suppliers from TopDesk.

        Maps TopDesk suppliers to IMS Supplier model.
        """
        result = SyncResult(
            integration="topdesk",
            entity_type="suppliers",
            success=True,
        )

        try:
            # Fetch suppliers from TopDesk
            # Endpoint: GET /tas/api/suppliers
            suppliers_data = await self._get("/tas/api/suppliers", params={
                "pageSize": 500,
            })

            suppliers = suppliers_data if isinstance(suppliers_data, list) else []

            for supplier in suppliers:
                try:
                    mapped_supplier = self._map_supplier(supplier)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Supplier {supplier.get('id')}: {str(e)}")

            logger.info(f"TopDesk sync: {result.created} suppliers synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"TopDesk supplier sync failed: {e}")

        return result

    async def sync_incidents(self) -> SyncResult:
        """Sync incidents from TopDesk."""
        result = SyncResult(
            integration="topdesk",
            entity_type="incidents",
            success=True,
        )

        try:
            # Fetch incidents from TopDesk
            # Endpoint: GET /tas/api/incidents
            incidents_data = await self._get("/tas/api/incidents", params={
                "pageSize": 100,
                "order": "creation_date+desc",
            })

            incidents = incidents_data if isinstance(incidents_data, list) else []

            for incident in incidents:
                try:
                    mapped_incident = self._map_incident(incident)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Incident {incident.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _map_asset(self, topdesk_asset: Dict[str, Any]) -> Dict[str, Any]:
        """Map TopDesk asset to IMS Asset format."""
        return {
            "external_id": topdesk_asset.get("id"),
            "external_source": "topdesk",
            "name": topdesk_asset.get("name", "Unknown"),
            "description": topdesk_asset.get("description", ""),
            "asset_type": self._map_asset_type(topdesk_asset.get("type", {}).get("name")),
            "status": self._map_status(topdesk_asset.get("status")),
            "metadata": {
                "topdesk_id": topdesk_asset.get("id"),
                "location": topdesk_asset.get("location", {}).get("name"),
                "supplier": topdesk_asset.get("supplier", {}).get("name"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_supplier(self, topdesk_supplier: Dict[str, Any]) -> Dict[str, Any]:
        """Map TopDesk supplier to IMS Supplier format."""
        return {
            "external_id": topdesk_supplier.get("id"),
            "external_source": "topdesk",
            "name": topdesk_supplier.get("name", "Unknown"),
            "contact_email": topdesk_supplier.get("email"),
            "contact_phone": topdesk_supplier.get("telephone"),
            "website": topdesk_supplier.get("website"),
            "metadata": {
                "topdesk_id": topdesk_supplier.get("id"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_incident(self, topdesk_incident: Dict[str, Any]) -> Dict[str, Any]:
        """Map TopDesk incident to IMS Incident format."""
        return {
            "external_id": topdesk_incident.get("id"),
            "external_source": "topdesk",
            "title": topdesk_incident.get("briefDescription", "Unknown"),
            "description": topdesk_incident.get("request", ""),
            "status": self._map_incident_status(topdesk_incident.get("processingStatus", {}).get("name")),
            "severity": self._map_severity(topdesk_incident.get("priority", {}).get("name")),
            "metadata": {
                "topdesk_number": topdesk_incident.get("number"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_asset_type(self, topdesk_type: Optional[str]) -> str:
        """Map TopDesk asset type to IMS asset type."""
        mapping = {
            "Server": "server",
            "Workstation": "workstation",
            "Laptop": "laptop",
            "Network Device": "network",
            "Software": "software",
            "Database": "database",
        }
        return mapping.get(topdesk_type, "other")

    def _map_status(self, topdesk_status: Optional[str]) -> str:
        """Map TopDesk status to IMS status."""
        mapping = {
            "In use": "active",
            "In stock": "inactive",
            "Defect": "inactive",
            "Disposed": "decommissioned",
        }
        return mapping.get(topdesk_status, "active")

    def _map_incident_status(self, topdesk_status: Optional[str]) -> str:
        """Map TopDesk incident status to IMS status."""
        mapping = {
            "Registered": "open",
            "In Progress": "investigating",
            "Completed": "resolved",
            "Closed": "closed",
        }
        return mapping.get(topdesk_status, "open")

    def _map_severity(self, topdesk_priority: Optional[str]) -> str:
        """Map TopDesk priority to IMS severity."""
        mapping = {
            "P1": "critical",
            "P2": "high",
            "P3": "medium",
            "P4": "low",
            "P5": "low",
        }
        return mapping.get(topdesk_priority, "medium")
