"""
Risicokader (Risk Framework) Endpoints — Hiaat 3
Manages risk assessment frameworks with impact/likelihood definitions.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import TenantCRUDBase
from app.core.rbac import require_admin, get_tenant_id
from app.models.core_models import (
    RiskFramework,
    RiskFrameworkStatus,
    User,
)

router = APIRouter()
crud_framework = TenantCRUDBase(RiskFramework)


# =============================================================================
# RISK FRAMEWORK CRUD
# =============================================================================

@router.get("/", response_model=List[RiskFramework])
async def list_risk_frameworks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[RiskFrameworkStatus] = Query(None),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """List risk frameworks."""
    filters = {}
    if status:
        filters["status"] = status

    return await crud_framework.get_multi(session, tenant_id, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=RiskFramework)
async def create_risk_framework(
    framework: RiskFramework,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create a new risk framework."""
    return await crud_framework.create(session, obj_in=framework, tenant_id=tenant_id)


@router.get("/active", response_model=Optional[RiskFramework])
async def get_active_framework(
    scope_id: Optional[int] = Query(None),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the active risk framework for a tenant (optionally scoped).
    Falls back to tenant-level if no scope-specific framework exists.
    """
    # Try scope-specific first
    if scope_id:
        result = await session.execute(
            select(RiskFramework).where(
                RiskFramework.tenant_id == tenant_id,
                RiskFramework.scope_id == scope_id,
                RiskFramework.status == RiskFrameworkStatus.ACTIVE,
            )
        )
        framework = result.scalars().first()
        if framework:
            return framework

    # Fall back to tenant-level (scope_id is NULL)
    result = await session.execute(
        select(RiskFramework).where(
            RiskFramework.tenant_id == tenant_id,
            RiskFramework.scope_id == None,
            RiskFramework.status == RiskFrameworkStatus.ACTIVE,
        )
    )
    return result.scalars().first()


@router.get("/{framework_id}", response_model=RiskFramework)
async def get_risk_framework(
    framework_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a risk framework by ID."""
    return await crud_framework.get_or_404(session, framework_id, tenant_id)


@router.patch("/{framework_id}", response_model=RiskFramework)
async def update_risk_framework(
    framework_id: int,
    framework_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Update a risk framework (only in Draft status)."""
    db_framework = await crud_framework.get_or_404(session, framework_id, tenant_id)

    if db_framework.status != RiskFrameworkStatus.DRAFT:
        # Only allow status changes for non-draft frameworks
        allowed_fields = {"status", "updated_at"}
        non_allowed = set(framework_update.keys()) - allowed_fields
        if non_allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update {non_allowed} when framework is {db_framework.status}. Create a new version."
            )

    framework_update["updated_at"] = datetime.utcnow()
    return await crud_framework.update(session, db_obj=db_framework, obj_in=framework_update, tenant_id=tenant_id)


@router.delete("/{framework_id}")
async def delete_risk_framework(
    framework_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Delete a risk framework (only Draft)."""
    db_framework = await crud_framework.get_or_404(session, framework_id, tenant_id)
    if db_framework.status != RiskFrameworkStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft frameworks can be deleted. Archive active ones instead."
        )
    deleted = await crud_framework.delete(session, id=framework_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Framework not found")
    return {"message": "Risk framework deleted"}


# =============================================================================
# FRAMEWORK LIFECYCLE
# =============================================================================

@router.post("/{framework_id}/activate", response_model=RiskFramework)
async def activate_risk_framework(
    framework_id: int,
    established_by_id: int = Query(..., description="User ID (management) who establishes the framework"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """
    Activate a risk framework.
    Deactivates any other active framework for the same tenant/scope.
    """
    db_framework = await crud_framework.get_or_404(session, framework_id, tenant_id)

    if db_framework.status != RiskFrameworkStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Only draft frameworks can be activated. Current: {db_framework.status}"
        )

    # Deactivate existing active frameworks for same tenant/scope
    query = select(RiskFramework).where(
        RiskFramework.tenant_id == db_framework.tenant_id,
        RiskFramework.status == RiskFrameworkStatus.ACTIVE,
    )
    if db_framework.scope_id:
        query = query.where(RiskFramework.scope_id == db_framework.scope_id)
    else:
        query = query.where(RiskFramework.scope_id == None)

    result = await session.execute(query)
    for existing in result.scalars().all():
        existing.status = RiskFrameworkStatus.ARCHIVED
        session.add(existing)

    return await crud_framework.update(session, db_obj=db_framework, obj_in={
        "status": RiskFrameworkStatus.ACTIVE,
        "established_by_id": established_by_id,
        "established_date": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }, tenant_id=tenant_id)


@router.post("/{framework_id}/archive", response_model=RiskFramework)
async def archive_risk_framework(
    framework_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Archive a risk framework."""
    db_framework = await crud_framework.get_or_404(session, framework_id, tenant_id)

    if db_framework.status != RiskFrameworkStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Only active frameworks can be archived. Current: {db_framework.status}"
        )

    return await crud_framework.update(session, db_obj=db_framework, obj_in={
        "status": RiskFrameworkStatus.ARCHIVED,
        "updated_at": datetime.utcnow(),
    }, tenant_id=tenant_id)


@router.post("/{framework_id}/new-version", response_model=RiskFramework)
async def create_new_version(
    framework_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    """Create a new draft version of an active or archived framework."""
    db_framework = await crud_framework.get_or_404(session, framework_id, tenant_id)

    new_framework = RiskFramework(
        tenant_id=db_framework.tenant_id,
        scope_id=db_framework.scope_id,
        name=db_framework.name,
        version=db_framework.version + 1,
        status=RiskFrameworkStatus.DRAFT,
        impact_definitions=db_framework.impact_definitions,
        likelihood_definitions=db_framework.likelihood_definitions,
        risk_tolerance=db_framework.risk_tolerance,
        decision_rules=db_framework.decision_rules,
    )

    return await crud_framework.create(session, obj_in=new_framework, tenant_id=tenant_id)
