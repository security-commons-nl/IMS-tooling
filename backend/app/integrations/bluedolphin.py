"""
BlueDolphin Integration Client

Syncs enterprise architecture data: applications, processes, data objects.
API Docs: https://www.bluedolphin.app/
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from app.integrations.base import BaseIntegration, IntegrationConfig, SyncResult

logger = logging.getLogger(__name__)


class BlueDolphinClient(BaseIntegration):
    """
    BlueDolphin API client for syncing enterprise architecture data.

    Supported entities:
    - Applications
    - Business Processes
    - Data Objects
    - Technologies
    - Integrations/Interfaces
    """

    async def test_connection(self) -> bool:
        """Test connection to BlueDolphin API."""
        try:
            await self._get("/api/v1/me")
            return True
        except Exception as e:
            logger.error(f"BlueDolphin connection test failed: {e}")
            return False

    async def sync_assets(self) -> SyncResult:
        """
        Sync applications as assets from BlueDolphin.

        Maps BlueDolphin applications to IMS Asset model.
        """
        result = SyncResult(
            integration="bluedolphin",
            entity_type="assets",
            success=True,
        )

        try:
            # Fetch applications from BlueDolphin
            response = await self._get("/api/v1/objects", params={
                "type": "application",
                "limit": 1000,
            })

            applications = response.get("items", [])

            for app in applications:
                try:
                    mapped_asset = self._map_application(app)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Application {app.get('id')}: {str(e)}")

            logger.info(f"BlueDolphin sync: {result.created} applications synced")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            logger.error(f"BlueDolphin application sync failed: {e}")

        return result

    async def sync_suppliers(self) -> SyncResult:
        """
        BlueDolphin can have vendor/technology providers.
        """
        result = SyncResult(
            integration="bluedolphin",
            entity_type="suppliers",
            success=True,
        )

        try:
            # Fetch technology vendors
            response = await self._get("/api/v1/objects", params={
                "type": "vendor",
                "limit": 500,
            })

            vendors = response.get("items", [])

            for vendor in vendors:
                try:
                    mapped_supplier = self._map_vendor(vendor)
                    # TODO: Upsert to database
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Vendor {vendor.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_processes(self) -> SyncResult:
        """Sync business processes from BlueDolphin."""
        result = SyncResult(
            integration="bluedolphin",
            entity_type="processes",
            success=True,
        )

        try:
            response = await self._get("/api/v1/objects", params={
                "type": "business_process",
                "limit": 500,
            })

            processes = response.get("items", [])

            for process in processes:
                try:
                    mapped_process = self._map_process(process)
                    # TODO: Upsert as Scope with type=process
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Process {process.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_data_objects(self) -> SyncResult:
        """Sync data objects from BlueDolphin (for privacy/PIMS)."""
        result = SyncResult(
            integration="bluedolphin",
            entity_type="data_objects",
            success=True,
        )

        try:
            response = await self._get("/api/v1/objects", params={
                "type": "data_object",
                "limit": 500,
            })

            data_objects = response.get("items", [])

            for data_obj in data_objects:
                try:
                    # Map to IMS data model (for privacy register)
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"DataObject {data_obj.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_integrations(self) -> SyncResult:
        """Sync integration/interface definitions from BlueDolphin."""
        result = SyncResult(
            integration="bluedolphin",
            entity_type="integrations",
            success=True,
        )

        try:
            response = await self._get("/api/v1/relations", params={
                "type": "integration",
                "limit": 500,
            })

            integrations = response.get("items", [])

            for integration in integrations:
                try:
                    # Map to IMS (useful for data flow analysis)
                    result.created += 1
                except Exception as e:
                    result.errors.append(f"Integration {integration.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    def _map_application(self, bd_app: Dict[str, Any]) -> Dict[str, Any]:
        """Map BlueDolphin application to IMS Asset format."""
        properties = bd_app.get("properties", {})

        return {
            "external_id": bd_app.get("id"),
            "external_source": "bluedolphin",
            "name": bd_app.get("name", "Unknown"),
            "description": bd_app.get("description", ""),
            "asset_type": "application",
            "status": self._map_lifecycle_status(properties.get("lifecycle_status")),
            "classification": self._map_classification(properties.get("data_classification")),
            "metadata": {
                "bluedolphin_id": bd_app.get("id"),
                "owner": properties.get("owner"),
                "business_criticality": properties.get("business_criticality"),
                "technology_stack": properties.get("technology"),
                "hosting": properties.get("hosting_type"),
                "vendor": properties.get("vendor"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_vendor(self, bd_vendor: Dict[str, Any]) -> Dict[str, Any]:
        """Map BlueDolphin vendor to IMS Supplier format."""
        properties = bd_vendor.get("properties", {})

        return {
            "external_id": bd_vendor.get("id"),
            "external_source": "bluedolphin",
            "name": bd_vendor.get("name", "Unknown"),
            "description": bd_vendor.get("description", ""),
            "website": properties.get("website"),
            "metadata": {
                "bluedolphin_id": bd_vendor.get("id"),
                "vendor_type": properties.get("type"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_process(self, bd_process: Dict[str, Any]) -> Dict[str, Any]:
        """Map BlueDolphin process to IMS Scope format."""
        properties = bd_process.get("properties", {})

        return {
            "external_id": bd_process.get("id"),
            "external_source": "bluedolphin",
            "name": bd_process.get("name", "Unknown"),
            "description": bd_process.get("description", ""),
            "scope_type": "process",
            "metadata": {
                "bluedolphin_id": bd_process.get("id"),
                "owner": properties.get("owner"),
                "department": properties.get("department"),
            },
            "last_synced": datetime.utcnow(),
        }

    def _map_lifecycle_status(self, status: Optional[str]) -> str:
        """Map BlueDolphin lifecycle status to IMS status."""
        mapping = {
            "in_development": "inactive",
            "production": "active",
            "phase_out": "active",
            "retired": "decommissioned",
            "planned": "inactive",
        }
        return mapping.get(str(status).lower() if status else "", "active")

    def _map_classification(self, classification: Optional[str]) -> str:
        """Map BlueDolphin data classification to IMS classification."""
        mapping = {
            "public": "public",
            "internal": "internal",
            "confidential": "confidential",
            "secret": "secret",
            "top_secret": "top_secret",
        }
        return mapping.get(str(classification).lower() if classification else "", "internal")
