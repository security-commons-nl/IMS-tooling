"""
Stakeholder Management Endpoints
ISO 27001 Clause 4.2: Understanding the needs and expectations of interested parties.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.crud import TenantCRUDBase
from app.core.rbac import require_configurer, get_tenant_id
from app.models.core_models import Stakeholder

router = APIRouter()
crud_stakeholder = TenantCRUDBase(Stakeholder)


@router.get("/", response_model=List[Stakeholder])
async def list_stakeholders(
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """List all stakeholders for the current tenant."""
    return await crud_stakeholder.get_multi(session, tenant_id, skip=skip, limit=limit)


@router.post("/", response_model=Stakeholder)
async def create_stakeholder(
    *,
    stakeholder_in: Stakeholder,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    _=Depends(require_configurer),
):
    """Create a new stakeholder."""
    return await crud_stakeholder.create(session, stakeholder_in, tenant_id)


@router.get("/{stakeholder_id}", response_model=Stakeholder)
async def get_stakeholder(
    stakeholder_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a single stakeholder by ID."""
    obj = await crud_stakeholder.get(session, stakeholder_id, tenant_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    return obj


@router.put("/{stakeholder_id}", response_model=Stakeholder)
async def update_stakeholder(
    stakeholder_id: int,
    stakeholder_in: Stakeholder,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    _=Depends(require_configurer),
):
    """Update a stakeholder."""
    obj = await crud_stakeholder.get(session, stakeholder_id, tenant_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    return await crud_stakeholder.update(session, obj, stakeholder_in)


@router.delete("/{stakeholder_id}", response_model=Stakeholder)
async def delete_stakeholder(
    stakeholder_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    _=Depends(require_configurer),
):
    """Delete a stakeholder."""
    obj = await crud_stakeholder.get(session, stakeholder_id, tenant_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
    return await crud_stakeholder.delete(session, obj)
