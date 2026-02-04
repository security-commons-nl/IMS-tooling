"""
Sync Orchestrator

Coordinates syncing between external integrations and the database.
Handles fetching from external systems and upserting to the database.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from app.integrations.base import IntegrationConfig, SyncResult
from app.integrations.topdesk import TopDeskClient
from app.integrations.servicenow import ServiceNowClient
from app.integrations.proquro import ProquroClient
from app.integrations.bluedolphin import BlueDolphinClient
from app.services.integration_service import integration_service

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """
    Orchestrates sync operations between external systems and the IMS database.

    This class handles:
    1. Fetching data from external systems via integration clients
    2. Mapping the data to IMS format
    3. Upserting to the database via integration_service
    """

    def __init__(self, session: AsyncSession, tenant_id: int):
        """
        Initialize the orchestrator.

        Args:
            session: Database session for upserts
            tenant_id: Tenant ID to associate synced records with
        """
        self.session = session
        self.tenant_id = tenant_id

    # =========================================================================
    # TOPDESK
    # =========================================================================

    async def sync_topdesk(
        self,
        config: IntegrationConfig,
        entity_types: Optional[List[str]] = None,
    ) -> List[SyncResult]:
        """Sync all configured entity types from TopDesk."""
        results = []
        sync_all = entity_types is None or "all" in entity_types

        async with TopDeskClient(config) as client:
            if not await client.test_connection():
                return [SyncResult(
                    integration="topdesk",
                    entity_type="connection",
                    success=False,
                    errors=["Connection test failed"],
                )]

            if sync_all or "assets" in entity_types:
                result = await self._sync_topdesk_assets(client)
                results.append(result)

            if sync_all or "suppliers" in entity_types:
                result = await self._sync_topdesk_suppliers(client)
                results.append(result)

            if sync_all or "incidents" in entity_types:
                result = await self._sync_topdesk_incidents(client)
                results.append(result)

        return results

    async def _sync_topdesk_assets(self, client: TopDeskClient) -> SyncResult:
        """Sync assets from TopDesk."""
        result = SyncResult(integration="topdesk", entity_type="assets", success=True)

        try:
            assets_data = await client._get("/tas/api/assetmgmt/assets", params={
                "fields": "id,name,type,status,supplier,location",
                "pageSize": 1000,
            })

            assets = assets_data.get("dataSet", [])

            for asset in assets:
                try:
                    mapped = client._map_asset(asset)
                    _, created = await integration_service.upsert_asset(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="topdesk",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Asset {asset.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_topdesk_suppliers(self, client: TopDeskClient) -> SyncResult:
        """Sync suppliers from TopDesk."""
        result = SyncResult(integration="topdesk", entity_type="suppliers", success=True)

        try:
            suppliers_data = await client._get("/tas/api/suppliers", params={
                "pageSize": 500,
            })

            suppliers = suppliers_data if isinstance(suppliers_data, list) else []

            for supplier in suppliers:
                try:
                    mapped = client._map_supplier(supplier)
                    _, created = await integration_service.upsert_supplier(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="topdesk",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Supplier {supplier.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_topdesk_incidents(self, client: TopDeskClient) -> SyncResult:
        """Sync incidents from TopDesk."""
        result = SyncResult(integration="topdesk", entity_type="incidents", success=True)

        try:
            incidents_data = await client._get("/tas/api/incidents", params={
                "pageSize": 100,
                "order": "creation_date+desc",
            })

            incidents = incidents_data if isinstance(incidents_data, list) else []

            for incident in incidents:
                try:
                    mapped = client._map_incident(incident)
                    mapped["external_reference"] = incident.get("number")
                    _, created = await integration_service.upsert_incident(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="topdesk",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Incident {incident.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    # =========================================================================
    # SERVICENOW
    # =========================================================================

    async def sync_servicenow(
        self,
        config: IntegrationConfig,
        entity_types: Optional[List[str]] = None,
    ) -> List[SyncResult]:
        """Sync all configured entity types from ServiceNow."""
        results = []
        sync_all = entity_types is None or "all" in entity_types

        async with ServiceNowClient(config) as client:
            if not await client.test_connection():
                return [SyncResult(
                    integration="servicenow",
                    entity_type="connection",
                    success=False,
                    errors=["Connection test failed"],
                )]

            if sync_all or "assets" in entity_types:
                result = await self._sync_servicenow_assets(client)
                results.append(result)

            if sync_all or "suppliers" in entity_types:
                result = await self._sync_servicenow_suppliers(client)
                results.append(result)

            if sync_all or "incidents" in entity_types:
                result = await self._sync_servicenow_incidents(client)
                results.append(result)

        return results

    async def _sync_servicenow_assets(self, client: ServiceNowClient) -> SyncResult:
        """Sync CMDB assets from ServiceNow."""
        result = SyncResult(integration="servicenow", entity_type="assets", success=True)

        try:
            response = await client._get("/api/now/table/cmdb_ci", params={
                "sysparm_fields": "sys_id,name,sys_class_name,operational_status,vendor,location",
                "sysparm_limit": 1000,
            })

            assets = response.get("result", [])

            for asset in assets:
                try:
                    mapped = client._map_asset(asset)
                    _, created = await integration_service.upsert_asset(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="servicenow",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"CI {asset.get('sys_id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_servicenow_suppliers(self, client: ServiceNowClient) -> SyncResult:
        """Sync vendors from ServiceNow."""
        result = SyncResult(integration="servicenow", entity_type="suppliers", success=True)

        try:
            response = await client._get("/api/now/table/core_company", params={
                "sysparm_query": "vendor=true",
                "sysparm_fields": "sys_id,name,email,phone,website",
                "sysparm_limit": 500,
            })

            suppliers = response.get("result", [])

            for supplier in suppliers:
                try:
                    mapped = client._map_supplier(supplier)
                    _, created = await integration_service.upsert_supplier(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="servicenow",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Vendor {supplier.get('sys_id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_servicenow_incidents(self, client: ServiceNowClient) -> SyncResult:
        """Sync incidents from ServiceNow."""
        result = SyncResult(integration="servicenow", entity_type="incidents", success=True)

        try:
            response = await client._get("/api/now/table/incident", params={
                "sysparm_fields": "sys_id,number,short_description,description,state,priority",
                "sysparm_limit": 100,
            })

            incidents = response.get("result", [])

            for incident in incidents:
                try:
                    mapped = client._map_incident(incident)
                    mapped["external_reference"] = incident.get("number")
                    _, created = await integration_service.upsert_incident(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="servicenow",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Incident {incident.get('number')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    # =========================================================================
    # PROQURO
    # =========================================================================

    async def sync_proquro(
        self,
        config: IntegrationConfig,
        entity_types: Optional[List[str]] = None,
    ) -> List[SyncResult]:
        """Sync all configured entity types from Proquro."""
        results = []
        sync_all = entity_types is None or "all" in entity_types

        async with ProquroClient(config) as client:
            if not await client.test_connection():
                return [SyncResult(
                    integration="proquro",
                    entity_type="connection",
                    success=False,
                    errors=["Connection test failed"],
                )]

            if sync_all or "suppliers" in entity_types:
                result = await self._sync_proquro_suppliers(client)
                results.append(result)

        return results

    async def _sync_proquro_suppliers(self, client: ProquroClient) -> SyncResult:
        """Sync suppliers from Proquro."""
        result = SyncResult(integration="proquro", entity_type="suppliers", success=True)

        try:
            response = await client._get("/api/v1/suppliers", params={
                "limit": 500,
                "include": "contracts,risks,contacts",
            })

            suppliers = response.get("data", [])

            for supplier in suppliers:
                try:
                    mapped = client._map_supplier(supplier)
                    _, created = await integration_service.upsert_supplier(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="proquro",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Supplier {supplier.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    # =========================================================================
    # BLUEDOLPHIN
    # =========================================================================

    async def sync_bluedolphin(
        self,
        config: IntegrationConfig,
        entity_types: Optional[List[str]] = None,
    ) -> List[SyncResult]:
        """Sync all configured entity types from BlueDolphin."""
        results = []
        sync_all = entity_types is None or "all" in entity_types

        async with BlueDolphinClient(config) as client:
            if not await client.test_connection():
                return [SyncResult(
                    integration="bluedolphin",
                    entity_type="connection",
                    success=False,
                    errors=["Connection test failed"],
                )]

            if sync_all or "assets" in entity_types:
                result = await self._sync_bluedolphin_assets(client)
                results.append(result)

            if sync_all or "suppliers" in entity_types:
                result = await self._sync_bluedolphin_suppliers(client)
                results.append(result)

            if sync_all or "processes" in entity_types:
                result = await self._sync_bluedolphin_processes(client)
                results.append(result)

        return results

    async def _sync_bluedolphin_assets(self, client: BlueDolphinClient) -> SyncResult:
        """Sync applications as assets from BlueDolphin."""
        result = SyncResult(integration="bluedolphin", entity_type="assets", success=True)

        try:
            response = await client._get("/api/v1/objects", params={
                "type": "application",
                "limit": 1000,
            })

            applications = response.get("items", [])

            for app in applications:
                try:
                    mapped = client._map_application(app)
                    _, created = await integration_service.upsert_asset(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="bluedolphin",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Application {app.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_bluedolphin_suppliers(self, client: BlueDolphinClient) -> SyncResult:
        """Sync vendors from BlueDolphin."""
        result = SyncResult(integration="bluedolphin", entity_type="suppliers", success=True)

        try:
            response = await client._get("/api/v1/objects", params={
                "type": "vendor",
                "limit": 500,
            })

            vendors = response.get("items", [])

            for vendor in vendors:
                try:
                    mapped = client._map_vendor(vendor)
                    _, created = await integration_service.upsert_supplier(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="bluedolphin",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Vendor {vendor.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _sync_bluedolphin_processes(self, client: BlueDolphinClient) -> SyncResult:
        """Sync business processes from BlueDolphin."""
        result = SyncResult(integration="bluedolphin", entity_type="processes", success=True)

        try:
            response = await client._get("/api/v1/objects", params={
                "type": "business_process",
                "limit": 500,
            })

            processes = response.get("items", [])

            for process in processes:
                try:
                    mapped = client._map_process(process)
                    _, created = await integration_service.upsert_process(
                        session=self.session,
                        tenant_id=self.tenant_id,
                        external_id=mapped["external_id"],
                        external_source="bluedolphin",
                        data=mapped,
                    )
                    if created:
                        result.created += 1
                    else:
                        result.updated += 1
                except Exception as e:
                    result.errors.append(f"Process {process.get('id')}: {str(e)}")

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result
