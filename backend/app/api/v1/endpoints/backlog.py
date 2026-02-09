from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.crud import TenantCRUDBase
from app.core.rbac import require_editor, get_tenant_id
from app.models.core_models import (
    BacklogItem,
    BacklogStatus,
    BacklogType,
    BacklogPriority,
    User,
)

router = APIRouter()
crud_backlog = TenantCRUDBase(BacklogItem)

@router.get("/", response_model=List[BacklogItem])
async def read_backlog_items(
    skip: int = 0,
    limit: int = 100,
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Retrieve backlog items.
    """
    query = select(BacklogItem).where(BacklogItem.tenant_id == tenant_id)

    if item_type:
        query = query.where(BacklogItem.item_type == item_type)
    if status:
        query = query.where(BacklogItem.status == status)
    if priority:
        query = query.where(BacklogItem.priority == priority)

    # Order by priority (Critical first) and then date
    query = query.order_by(BacklogItem.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await session.execute(query)
    items = result.scalars().all()
    return items


@router.post("/", response_model=BacklogItem)
async def create_backlog_item(
    *,
    item_in: BacklogItem,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
) -> Any:
    """
    Create new backlog item.
    """
    return await crud_backlog.create(session, obj_in=item_in, tenant_id=tenant_id)


@router.get("/{id}", response_model=BacklogItem)
async def read_backlog_item(
    *,
    id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get backlog item by ID.
    """
    return await crud_backlog.get_or_404(session, id, tenant_id)


@router.patch("/{id}", response_model=BacklogItem)
async def update_backlog_item(
    *,
    id: int,
    item_in: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
) -> Any:
    """
    Update backlog item.
    """
    db_item = await crud_backlog.get_or_404(session, id, tenant_id)
    return await crud_backlog.update(session, db_obj=db_item, obj_in=item_in, tenant_id=tenant_id)


@router.delete("/{id}", response_model=dict)
async def delete_backlog_item(
    *,
    id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
) -> Any:
    """
    Delete backlog item.
    """
    await crud_backlog.get_or_404(session, id, tenant_id)
    deleted = await crud_backlog.delete(session, id=id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    return {"ok": True}
