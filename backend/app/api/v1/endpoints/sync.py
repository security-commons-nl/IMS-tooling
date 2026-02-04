"""
Sync Endpoints

Manual and scheduled sync operations with external systems.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session, async_engine
from app.integrations import IntegrationConfig
from app.integrations.base import SyncResult
from app.services.sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


class IntegrationType(str, Enum):
    TOPDESK = "topdesk"
    SERVICENOW = "servicenow"
    PROQURO = "proquro"
    BLUEDOLPHIN = "bluedolphin"


class SyncRequest(BaseModel):
    integration: IntegrationType
    entity_types: Optional[List[str]] = None  # None = all
    tenant_id: int = 1  # Default tenant


class IntegrationStatus(BaseModel):
    name: str
    enabled: bool
    connected: bool
    last_sync: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    created: int = 0
    updated: int = 0
    errors: int = 0


# In-memory store for sync status (should be in DB in production)
_sync_status: Dict[str, Dict] = {}


def get_integration_config(integration: IntegrationType) -> Optional[IntegrationConfig]:
    """
    Get integration configuration from settings.
    """
    from app.core.config import settings

    configs = {
        IntegrationType.TOPDESK: IntegrationConfig(
            name="TopDesk",
            base_url=settings.TOPDESK_URL or "",
            username=settings.TOPDESK_USERNAME,
            password=settings.TOPDESK_PASSWORD,
            enabled=bool(settings.TOPDESK_URL),
        ),
        IntegrationType.SERVICENOW: IntegrationConfig(
            name="ServiceNow",
            base_url=settings.SERVICENOW_URL or "",
            username=settings.SERVICENOW_USERNAME,
            password=settings.SERVICENOW_PASSWORD,
            enabled=bool(settings.SERVICENOW_URL),
        ),
        IntegrationType.PROQURO: IntegrationConfig(
            name="Proquro",
            base_url=settings.PROQURO_URL or "",
            api_key=settings.PROQURO_API_KEY,
            enabled=bool(settings.PROQURO_URL),
        ),
        IntegrationType.BLUEDOLPHIN: IntegrationConfig(
            name="BlueDolphin",
            base_url=settings.BLUEDOLPHIN_URL or "",
            api_key=settings.BLUEDOLPHIN_API_KEY,
            enabled=bool(settings.BLUEDOLPHIN_URL),
        ),
    }

    return configs.get(integration)


# =============================================================================
# Status Endpoints
# =============================================================================

@router.get("/status")
async def get_all_integration_status() -> List[IntegrationStatus]:
    """Get status of all configured integrations."""
    statuses = []

    for integration in IntegrationType:
        config = get_integration_config(integration)
        sync_info = _sync_status.get(integration.value, {})

        statuses.append(IntegrationStatus(
            name=integration.value,
            enabled=config.enabled if config else False,
            connected=sync_info.get("connected", False),
            last_sync=sync_info.get("last_sync"),
            last_sync_status=sync_info.get("status"),
            created=sync_info.get("created", 0),
            updated=sync_info.get("updated", 0),
            errors=sync_info.get("errors", 0),
        ))

    return statuses


@router.get("/status/{integration}")
async def get_integration_status(integration: IntegrationType) -> IntegrationStatus:
    """Get status of a specific integration."""
    config = get_integration_config(integration)
    sync_info = _sync_status.get(integration.value, {})

    return IntegrationStatus(
        name=integration.value,
        enabled=config.enabled if config else False,
        connected=sync_info.get("connected", False),
        last_sync=sync_info.get("last_sync"),
        last_sync_status=sync_info.get("status"),
        created=sync_info.get("created", 0),
        updated=sync_info.get("updated", 0),
        errors=sync_info.get("errors", 0),
    )


# =============================================================================
# Connection Test Endpoints
# =============================================================================

@router.post("/test/{integration}")
async def test_integration_connection(integration: IntegrationType) -> Dict[str, Any]:
    """Test connection to an external integration."""
    from app.integrations import TopDeskClient, ServiceNowClient, ProquroClient, BlueDolphinClient

    config = get_integration_config(integration)

    if not config or not config.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Integration {integration.value} is not configured"
        )

    clients = {
        IntegrationType.TOPDESK: TopDeskClient,
        IntegrationType.SERVICENOW: ServiceNowClient,
        IntegrationType.PROQURO: ProquroClient,
        IntegrationType.BLUEDOLPHIN: BlueDolphinClient,
    }

    async with clients[integration](config) as client:
        connected = await client.test_connection()

        _sync_status[integration.value] = {
            **_sync_status.get(integration.value, {}),
            "connected": connected,
            "last_test": datetime.utcnow(),
        }

        return {
            "integration": integration.value,
            "connected": connected,
            "timestamp": datetime.utcnow().isoformat(),
        }


# =============================================================================
# Manual Sync Endpoints
# =============================================================================

@router.post("/run/{integration}")
async def run_sync(
    integration: IntegrationType,
    background_tasks: BackgroundTasks,
    tenant_id: int = Query(default=1, description="Tenant ID to sync data for"),
    entity_types: Optional[List[str]] = Query(default=None, description="Entity types to sync"),
) -> Dict[str, Any]:
    """
    Trigger a manual sync for an integration.

    Runs in background and returns immediately.
    """
    config = get_integration_config(integration)

    if not config or not config.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Integration {integration.value} is not configured"
        )

    # Add sync task to background
    background_tasks.add_task(
        _run_sync_task,
        integration,
        config,
        tenant_id,
        entity_types,
    )

    return {
        "status": "started",
        "integration": integration.value,
        "tenant_id": tenant_id,
        "entity_types": entity_types or ["all"],
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _run_sync_task(
    integration: IntegrationType,
    config: IntegrationConfig,
    tenant_id: int,
    entity_types: Optional[List[str]] = None,
):
    """Background task to run sync with database persistence."""
    results: List[SyncResult] = []

    try:
        # Create a new database session for background task
        async with AsyncSession(async_engine) as session:
            orchestrator = SyncOrchestrator(session, tenant_id)

            # Run the appropriate sync based on integration type
            if integration == IntegrationType.TOPDESK:
                results = await orchestrator.sync_topdesk(config, entity_types)
            elif integration == IntegrationType.SERVICENOW:
                results = await orchestrator.sync_servicenow(config, entity_types)
            elif integration == IntegrationType.PROQURO:
                results = await orchestrator.sync_proquro(config, entity_types)
            elif integration == IntegrationType.BLUEDOLPHIN:
                results = await orchestrator.sync_bluedolphin(config, entity_types)

        # Calculate totals
        total_created = sum(r.created for r in results)
        total_updated = sum(r.updated for r in results)
        total_errors = sum(len(r.errors) for r in results)
        all_successful = all(r.success for r in results)

        _sync_status[integration.value] = {
            "connected": True,
            "last_sync": datetime.utcnow(),
            "status": "success" if all_successful and total_errors == 0 else "partial",
            "created": total_created,
            "updated": total_updated,
            "errors": total_errors,
        }

        logger.info(
            f"Sync completed for {integration.value}: "
            f"{total_created} created, {total_updated} updated, {total_errors} errors"
        )

    except Exception as e:
        logger.error(f"Sync failed for {integration.value}: {e}")
        _sync_status[integration.value] = {
            **_sync_status.get(integration.value, {}),
            "last_sync": datetime.utcnow(),
            "status": "failed",
            "error": str(e),
        }


# =============================================================================
# Sync All
# =============================================================================

@router.post("/run-all")
async def run_all_syncs(
    background_tasks: BackgroundTasks,
    tenant_id: int = Query(default=1, description="Tenant ID to sync data for"),
) -> Dict[str, Any]:
    """Trigger sync for all enabled integrations."""
    started = []

    for integration in IntegrationType:
        config = get_integration_config(integration)
        if config and config.enabled:
            background_tasks.add_task(
                _run_sync_task,
                integration,
                config,
                tenant_id,
                None,
            )
            started.append(integration.value)

    return {
        "status": "started",
        "integrations": started,
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Sync History
# =============================================================================

@router.get("/history/{integration}")
async def get_sync_history(
    integration: IntegrationType,
    limit: int = 10,
) -> Dict[str, Any]:
    """Get sync history for an integration."""
    # TODO: Store history in database
    current_status = _sync_status.get(integration.value, {})

    return {
        "integration": integration.value,
        "current_status": current_status,
        "history": [],  # TODO: Implement history from DB
    }
