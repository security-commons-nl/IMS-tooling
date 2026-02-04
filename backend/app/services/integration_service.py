"""
Integration Service

Handles database upsert operations for data synced from external systems
(TopDesk, ServiceNow, Proquro, BlueDolphin).
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging

from sqlalchemy import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.core_models import (
    Scope, ScopeType, AssetType, ClassificationLevel,
    Incident, Status, FindingSeverity,
)

logger = logging.getLogger(__name__)


class IntegrationService:
    """
    Service for upserting externally synced data to the database.

    All upsert methods return a tuple of (record, was_created).
    """

    # =========================================================================
    # ASSET UPSERT (Scope with type=ASSET)
    # =========================================================================

    async def upsert_asset(
        self,
        session: AsyncSession,
        tenant_id: int,
        external_id: str,
        external_source: str,
        data: Dict[str, Any],
    ) -> Tuple[Scope, bool]:
        """
        Upsert an asset from an external system.

        Args:
            session: Database session
            tenant_id: Tenant ID to associate the asset with
            external_id: Unique identifier in the external system
            external_source: Source system (e.g., "topdesk", "servicenow")
            data: Mapped asset data with keys:
                - name: str (required)
                - description: str
                - asset_type: str (mapped to AssetType)
                - status: str ("active", "inactive", "decommissioned")
                - classification: str (mapped to ClassificationLevel)
                - location: str
                - metadata: dict (stored in description as JSON note)

        Returns:
            Tuple of (Scope record, was_created boolean)
        """
        # Find existing record by external_id + external_source
        stmt = select(Scope).where(
            and_(
                Scope.tenant_id == tenant_id,
                Scope.external_id == external_id,
                Scope.external_source == external_source,
            )
        )
        result = await session.exec(stmt)
        existing = result.first()

        # Map asset_type string to enum
        asset_type = self._map_asset_type(data.get("asset_type"))

        # Map classification string to enum
        classification = self._map_classification(data.get("classification"))

        # Map status to is_active
        is_active = data.get("status", "active") != "decommissioned"

        if existing:
            # Update existing record
            existing.name = data.get("name", existing.name)
            existing.description = data.get("description", existing.description)
            existing.asset_type = asset_type
            existing.location = data.get("location", existing.location)
            existing.data_classification = classification
            existing.is_active = is_active
            existing.last_synced = datetime.utcnow()
            existing.updated_at = datetime.utcnow()

            session.add(existing)
            await session.commit()
            await session.refresh(existing)

            logger.debug(f"Updated asset {external_id} from {external_source}")
            return existing, False
        else:
            # Create new record
            new_asset = Scope(
                tenant_id=tenant_id,
                name=data.get("name", "Unknown"),
                type=ScopeType.ASSET,
                description=data.get("description"),
                owner=data.get("owner", "Unassigned"),
                asset_type=asset_type,
                location=data.get("location"),
                data_classification=classification,
                is_active=is_active,
                external_id=external_id,
                external_source=external_source,
                last_synced=datetime.utcnow(),
            )

            session.add(new_asset)
            await session.commit()
            await session.refresh(new_asset)

            logger.debug(f"Created asset {external_id} from {external_source}")
            return new_asset, True

    # =========================================================================
    # SUPPLIER UPSERT (Scope with type=SUPPLIER)
    # =========================================================================

    async def upsert_supplier(
        self,
        session: AsyncSession,
        tenant_id: int,
        external_id: str,
        external_source: str,
        data: Dict[str, Any],
    ) -> Tuple[Scope, bool]:
        """
        Upsert a supplier from an external system.

        Args:
            session: Database session
            tenant_id: Tenant ID
            external_id: Unique identifier in the external system
            external_source: Source system (e.g., "proquro", "servicenow")
            data: Mapped supplier data with keys:
                - name: str (required)
                - description: str
                - contact_name: str
                - contact_email: str
                - contact_phone: str
                - website: str
                - status: str
                - risk_level: str

        Returns:
            Tuple of (Scope record, was_created boolean)
        """
        stmt = select(Scope).where(
            and_(
                Scope.tenant_id == tenant_id,
                Scope.external_id == external_id,
                Scope.external_source == external_source,
            )
        )
        result = await session.exec(stmt)
        existing = result.first()

        is_active = data.get("status", "active") not in ["inactive", "blocked", "archived"]

        if existing:
            existing.name = data.get("name", existing.name)
            existing.description = data.get("description", existing.description)
            existing.vendor_contact_name = data.get("contact_name", existing.vendor_contact_name)
            existing.vendor_contact_email = data.get("contact_email", existing.vendor_contact_email)
            existing.is_active = is_active
            existing.last_synced = datetime.utcnow()
            existing.updated_at = datetime.utcnow()

            session.add(existing)
            await session.commit()
            await session.refresh(existing)

            logger.debug(f"Updated supplier {external_id} from {external_source}")
            return existing, False
        else:
            new_supplier = Scope(
                tenant_id=tenant_id,
                name=data.get("name", "Unknown"),
                type=ScopeType.SUPPLIER,
                description=data.get("description"),
                owner=data.get("owner", "Unassigned"),
                vendor_contact_name=data.get("contact_name"),
                vendor_contact_email=data.get("contact_email"),
                is_active=is_active,
                external_id=external_id,
                external_source=external_source,
                last_synced=datetime.utcnow(),
            )

            session.add(new_supplier)
            await session.commit()
            await session.refresh(new_supplier)

            logger.debug(f"Created supplier {external_id} from {external_source}")
            return new_supplier, True

    # =========================================================================
    # INCIDENT UPSERT
    # =========================================================================

    async def upsert_incident(
        self,
        session: AsyncSession,
        tenant_id: int,
        external_id: str,
        external_source: str,
        data: Dict[str, Any],
    ) -> Tuple[Incident, bool]:
        """
        Upsert an incident from an external system.

        Args:
            session: Database session
            tenant_id: Tenant ID
            external_id: Unique identifier in the external system
            external_source: Source system (e.g., "topdesk", "servicenow")
            data: Mapped incident data with keys:
                - title: str (required)
                - description: str
                - status: str ("open", "investigating", "resolved", "closed")
                - severity: str ("critical", "high", "medium", "low")
                - external_reference: str (e.g., "INC-12345")

        Returns:
            Tuple of (Incident record, was_created boolean)
        """
        stmt = select(Incident).where(
            and_(
                Incident.tenant_id == tenant_id,
                Incident.external_id == external_id,
                Incident.external_source == external_source,
            )
        )
        result = await session.exec(stmt)
        existing = result.first()

        status = self._map_incident_status(data.get("status"))
        severity = self._map_severity(data.get("severity"))

        if existing:
            existing.title = data.get("title", existing.title)
            existing.description = data.get("description", existing.description)
            existing.status = status
            existing.severity = severity
            existing.external_reference = data.get("external_reference", existing.external_reference)
            existing.external_system = external_source.capitalize()
            existing.last_synced = datetime.utcnow()

            # Update resolution date if resolved
            if status in [Status.RESOLVED, Status.CLOSED] and not existing.date_resolved:
                existing.date_resolved = datetime.utcnow()

            session.add(existing)
            await session.commit()
            await session.refresh(existing)

            logger.debug(f"Updated incident {external_id} from {external_source}")
            return existing, False
        else:
            new_incident = Incident(
                tenant_id=tenant_id,
                title=data.get("title", "Unknown"),
                description=data.get("description", ""),
                status=status,
                severity=severity,
                incident_type="Security",  # Default, can be overridden
                external_id=external_id,
                external_source=external_source,
                external_system=external_source.capitalize(),
                external_reference=data.get("external_reference"),
                last_synced=datetime.utcnow(),
            )

            session.add(new_incident)
            await session.commit()
            await session.refresh(new_incident)

            logger.debug(f"Created incident {external_id} from {external_source}")
            return new_incident, True

    # =========================================================================
    # PROCESS UPSERT (Scope with type=PROCESS) - for BlueDolphin
    # =========================================================================

    async def upsert_process(
        self,
        session: AsyncSession,
        tenant_id: int,
        external_id: str,
        external_source: str,
        data: Dict[str, Any],
    ) -> Tuple[Scope, bool]:
        """
        Upsert a business process from an external system (BlueDolphin).

        Args:
            session: Database session
            tenant_id: Tenant ID
            external_id: Unique identifier in the external system
            external_source: Source system (e.g., "bluedolphin")
            data: Mapped process data with keys:
                - name: str (required)
                - description: str
                - owner: str

        Returns:
            Tuple of (Scope record, was_created boolean)
        """
        stmt = select(Scope).where(
            and_(
                Scope.tenant_id == tenant_id,
                Scope.external_id == external_id,
                Scope.external_source == external_source,
            )
        )
        result = await session.exec(stmt)
        existing = result.first()

        if existing:
            existing.name = data.get("name", existing.name)
            existing.description = data.get("description", existing.description)
            existing.owner = data.get("owner", existing.owner)
            existing.last_synced = datetime.utcnow()
            existing.updated_at = datetime.utcnow()

            session.add(existing)
            await session.commit()
            await session.refresh(existing)

            logger.debug(f"Updated process {external_id} from {external_source}")
            return existing, False
        else:
            new_process = Scope(
                tenant_id=tenant_id,
                name=data.get("name", "Unknown"),
                type=ScopeType.PROCESS,
                description=data.get("description"),
                owner=data.get("owner", "Unassigned"),
                external_id=external_id,
                external_source=external_source,
                last_synced=datetime.utcnow(),
            )

            session.add(new_process)
            await session.commit()
            await session.refresh(new_process)

            logger.debug(f"Created process {external_id} from {external_source}")
            return new_process, True

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _map_asset_type(self, type_str: Optional[str]) -> Optional[AssetType]:
        """Map string asset type to AssetType enum."""
        if not type_str:
            return None

        mapping = {
            "server": AssetType.HARDWARE,
            "workstation": AssetType.HARDWARE,
            "laptop": AssetType.HARDWARE,
            "hardware": AssetType.HARDWARE,
            "network": AssetType.NETWORK,
            "software": AssetType.SOFTWARE,
            "application": AssetType.SOFTWARE,
            "database": AssetType.DATA,
            "data": AssetType.DATA,
            "service": AssetType.SERVICE,
            "facility": AssetType.FACILITY,
            "people": AssetType.PEOPLE,
        }
        return mapping.get(type_str.lower(), AssetType.HARDWARE)

    def _map_classification(self, level_str: Optional[str]) -> Optional[ClassificationLevel]:
        """Map string classification to ClassificationLevel enum."""
        if not level_str:
            return None

        mapping = {
            "public": ClassificationLevel.PUBLIC,
            "internal": ClassificationLevel.INTERNAL,
            "confidential": ClassificationLevel.CONFIDENTIAL,
            "secret": ClassificationLevel.SECRET,
            "top_secret": ClassificationLevel.SECRET,
        }
        return mapping.get(level_str.lower(), ClassificationLevel.INTERNAL)

    def _map_incident_status(self, status_str: Optional[str]) -> Status:
        """Map string status to Status enum."""
        if not status_str:
            return Status.ACTIVE

        mapping = {
            "open": Status.ACTIVE,
            "new": Status.ACTIVE,
            "investigating": Status.ACTIVE,
            "in_progress": Status.ACTIVE,
            "resolved": Status.RESOLVED,
            "closed": Status.CLOSED,
        }
        return mapping.get(status_str.lower(), Status.ACTIVE)

    def _map_severity(self, severity_str: Optional[str]) -> FindingSeverity:
        """Map string severity to FindingSeverity enum."""
        if not severity_str:
            return FindingSeverity.MEDIUM

        mapping = {
            "critical": FindingSeverity.CRITICAL,
            "high": FindingSeverity.HIGH,
            "medium": FindingSeverity.MEDIUM,
            "low": FindingSeverity.LOW,
            "info": FindingSeverity.INFO,
        }
        return mapping.get(severity_str.lower(), FindingSeverity.MEDIUM)


# Singleton instance
integration_service = IntegrationService()
