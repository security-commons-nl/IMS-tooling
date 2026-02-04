"""
ServiceNow Integration Client

Syncs CMDB, incidents, and changes from ServiceNow.
API Docs: https://developer.servicenow.com/
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from app.integrations.base import BaseIntegration, IntegrationConfig, SyncResult

logger = logging.getLogger(__name__)


class ServiceNowClient(BaseIntegration):
    """
    ServiceNow API client for syncing ITSM/CMDB data.

    Supported entities:
    - CMDB Configuration Items (assets)
    - Incidents
    - Changes
    - Vendors (suppliers)
    """

    async def test_connection(self) -> bool:
        """Test connection to ServiceNow API."""
        try:
            await self._get("/api/now/table/sys_user?sysparm_limit=1")
            return True
        except Exception as e:
            logger.error(f"ServiceNow connection test failed: {e}")
            return False

    async def sync_assets(self) -> SyncResult:
        """
        Sync CMDB configuration items from ServiceNow.

        Uses the cmdb_ci table and related tables.
        """
        result = SyncResult(
            integration="servicenow",
            entity_type="assets",
            success=True,
        )

        try:
            # Fetch CIs from ServiceNow CMDB
            # Table: cmdb_ci (base) or specific like cmdb_ci_server
            response = await self._get("/api/now/table/cmdb_ci", params={
                "sysparm_fields": "sys_id,name,sys_class_name,operational_status,vendor,location",
                "sysparm_limit": 1000,
            })

            assets = response.get("result", [])

            for asset in assets:
                try:
                    mapped_asset = self._map_asset(asset)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"CI {asset.get('sys_id')}: {str(e)}")

            logger.info(f"ServiceNow sync: {result.created} assets synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"ServiceNow asset sync failed: {e}")

        return result

    async def sync_suppliers(self) -> SyncResult:
        """
        Sync vendors from ServiceNow.

        Uses the core_company table.
        """
        result = SyncResult(
            integration="servicenow",
            entity_type="suppliers",
            success=True,
        )

        try:
            # Fetch vendors from ServiceNow
            response = await self._get("/api/now/table/core_company", params={
                "sysparm_query": "vendor=true",
                "sysparm_fields": "sys_id,name,email,phone,website",
                "sysparm_limit": 500,
            })

            suppliers = response.get("result", [])

            for supplier in suppliers:
                try:
                    mapped_supplier = self._map_supplier(supplier)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Vendor {supplier.get('sys_id')}: {str(e)}")

            logger.info(f"ServiceNow sync: {result.created} suppliers synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"ServiceNow supplier sync failed: {e}")

        return result

    async def sync_incidents(self) -> SyncResult:
        """Sync incidents from ServiceNow."""
        result = SyncResult(
            integration="servicenow",
            entity_type="incidents",
            success=True,
        )

        try:
            response = await self._get("/api/now/table/incident", params={
                "sysparm_fields": "sys_id,number,short_description,description,state,priority,cmdb_ci",
                "sysparm_limit": 100,
                "sysparm_query": "ORDERBYDESCsys_created_on",
            })

            incidents = response.get("result", [])

            for incident in incidents:
                try:
                    mapped_incident = self._map_incident(incident)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Incident {incident.get('number')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_changes(self) -> SyncResult:
        """Sync change requests from ServiceNow."""
        result = SyncResult(
            integration="servicenow",
            entity_type="changes",
            success=True,
        )

        try:
            response = await self._get("/api/now/table/change_request", params={
                "sysparm_fields": "sys_id,number,short_description,state,risk,cmdb_ci",
                "sysparm_limit": 100,
            })

            changes = response.get("result", [])

            for change in changes:
                try:
                    # TODO: Map and upsert change
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Change {change.get('number')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _map_asset(self, snow_ci: Dict[str, Any]) -> Dict[str, Any]:
        """Map ServiceNow CI to IMS Asset format."""
        return {
            "external_id": snow_ci.get("sys_id"),
            "external_source": "servicenow",
            "name": snow_ci.get("name", "Unknown"),
            "description": snow_ci.get("short_description", ""),
            "asset_type": self._map_ci_class(snow_ci.get("sys_class_name")),
            "status": self._map_operational_status(snow_ci.get("operational_status")),
            "metadata": {
                "snow_sys_id": snow_ci.get("sys_id"),
                "snow_class": snow_ci.get("sys_class_name"),
                "location": snow_ci.get("location", {}).get("display_value") if isinstance(snow_ci.get("location"), dict) else None,
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_supplier(self, snow_vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Map ServiceNow vendor to IMS Supplier format."""
        return {
            "external_id": snow_vendor.get("sys_id"),
            "external_source": "servicenow",
            "name": snow_vendor.get("name", "Unknown"),
            "contact_email": snow_vendor.get("email"),
            "contact_phone": snow_vendor.get("phone"),
            "website": snow_vendor.get("website"),
            "metadata": {
                "snow_sys_id": snow_vendor.get("sys_id"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_incident(self, snow_incident: Dict[str, Any]) -> Dict[str, Any]:
        """Map ServiceNow incident to IMS Incident format."""
        return {
            "external_id": snow_incident.get("sys_id"),
            "external_source": "servicenow",
            "title": snow_incident.get("short_description", "Unknown"),
            "description": snow_incident.get("description", ""),
            "status": self._map_incident_state(snow_incident.get("state")),
            "severity": self._map_priority(snow_incident.get("priority")),
            "metadata": {
                "snow_number": snow_incident.get("number"),
                "snow_sys_id": snow_incident.get("sys_id"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_ci_class(self, sys_class: Optional[str]) -> str:
        """Map ServiceNow CI class to IMS asset type."""
        mapping = {
            "cmdb_ci_server": "server",
            "cmdb_ci_computer": "workstation",
            "cmdb_ci_pc_hardware": "workstation",
            "cmdb_ci_laptop": "laptop",
            "cmdb_ci_netgear": "network",
            "cmdb_ci_appl": "application",
            "cmdb_ci_database": "database",
            "cmdb_ci_service": "service",
        }
        return mapping.get(sys_class, "other")

    def _map_operational_status(self, status: Optional[str]) -> str:
        """Map ServiceNow operational status to IMS status."""
        mapping = {
            "1": "active",      # Operational
            "2": "inactive",    # Non-Operational
            "3": "inactive",    # Repair in Progress
            "4": "inactive",    # DR Standby
            "5": "inactive",    # Ready
            "6": "decommissioned",  # Retired
        }
        return mapping.get(str(status), "active")

    def _map_incident_state(self, state: Optional[str]) -> str:
        """Map ServiceNow incident state to IMS status."""
        mapping = {
            "1": "open",         # New
            "2": "investigating", # In Progress
            "3": "investigating", # On Hold
            "6": "resolved",     # Resolved
            "7": "closed",       # Closed
            "8": "closed",       # Cancelled
        }
        return mapping.get(str(state), "open")

    def _map_priority(self, priority: Optional[str]) -> str:
        """Map ServiceNow priority to IMS severity."""
        mapping = {
            "1": "critical",
            "2": "high",
            "3": "medium",
            "4": "low",
            "5": "low",
        }
        return mapping.get(str(priority), "medium")
