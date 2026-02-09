"""
Corrective Actions Endpoints (Verbeteracties)
Standalone CRUD for corrective actions with filtering, stats, complete/verify workflow.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.db import get_session
from app.core.crud import TenantCRUDBase
from app.core.rbac import require_editor, get_tenant_id
from app.models.core_models import CorrectiveAction, User

import logging

logger = logging.getLogger(__name__)

router = APIRouter()
crud_action = TenantCRUDBase(CorrectiveAction)


@router.get("/stats")
async def get_corrective_action_stats(
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get KPI statistics for corrective actions."""
    base = select(CorrectiveAction).where(CorrectiveAction.tenant_id == tenant_id)

    # Total
    total_q = select(func.count()).select_from(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id
    )
    total = (await session.execute(total_q)).scalar() or 0

    # Open (not completed)
    open_q = select(func.count()).select_from(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id,
        CorrectiveAction.completed == False,
    )
    open_count = (await session.execute(open_q)).scalar() or 0

    # Overdue (not completed, due_date < now)
    now = datetime.utcnow()
    overdue_q = select(func.count()).select_from(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id,
        CorrectiveAction.completed == False,
        CorrectiveAction.due_date != None,
        CorrectiveAction.due_date < now,
    )
    overdue_count = (await session.execute(overdue_q)).scalar() or 0

    # Completed
    completed_q = select(func.count()).select_from(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id,
        CorrectiveAction.completed == True,
    )
    completed_count = (await session.execute(completed_q)).scalar() or 0

    # Verified
    verified_q = select(func.count()).select_from(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id,
        CorrectiveAction.verified == True,
    )
    verified_count = (await session.execute(verified_q)).scalar() or 0

    return {
        "total": total,
        "open": open_count,
        "overdue": overdue_count,
        "completed": completed_count,
        "verified": verified_count,
    }


@router.get("/", response_model=List[CorrectiveAction])
async def list_corrective_actions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter: open/overdue/completed/verified"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW/MEDIUM/HIGH/CRITICAL)"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assignee"),
    source_type: Optional[str] = Query(None, description="Filter: finding/incident/issue/initiative/risk/control"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """List corrective actions with filters."""
    query = select(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id
    )

    # Status filter
    now = datetime.utcnow()
    if status == "open":
        query = query.where(CorrectiveAction.completed == False)
    elif status == "overdue":
        query = query.where(
            CorrectiveAction.completed == False,
            CorrectiveAction.due_date != None,
            CorrectiveAction.due_date < now,
        )
    elif status == "completed":
        query = query.where(CorrectiveAction.completed == True)
    elif status == "verified":
        query = query.where(CorrectiveAction.verified == True)

    # Priority filter
    if priority:
        query = query.where(CorrectiveAction.priority == priority)

    # Assignee filter
    if assigned_to_id:
        query = query.where(CorrectiveAction.assigned_to_id == assigned_to_id)

    # Source type filter
    if source_type == "finding":
        query = query.where(CorrectiveAction.finding_id != None)
    elif source_type == "incident":
        query = query.where(CorrectiveAction.incident_id != None)
    elif source_type == "issue":
        query = query.where(CorrectiveAction.issue_id != None)
    elif source_type == "initiative":
        query = query.where(CorrectiveAction.initiative_id != None)
    elif source_type == "risk":
        query = query.where(CorrectiveAction.risk_id != None)
    elif source_type == "control":
        query = query.where(CorrectiveAction.control_id != None)

    query = query.order_by(CorrectiveAction.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=CorrectiveAction)
async def create_corrective_action(
    action: CorrectiveAction,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Create a standalone corrective action."""
    return await crud_action.create(session, obj_in=action, tenant_id=tenant_id)


@router.get("/{action_id}", response_model=CorrectiveAction)
async def get_corrective_action(
    action_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a corrective action by ID."""
    return await crud_action.get_or_404(session, action_id, tenant_id)


@router.patch("/{action_id}", response_model=CorrectiveAction)
async def update_corrective_action(
    action_id: int,
    update_data: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Update a corrective action."""
    db_action = await crud_action.get_or_404(session, action_id, tenant_id)
    update_data["updated_at"] = datetime.utcnow()
    return await crud_action.update(session, db_obj=db_action, obj_in=update_data, tenant_id=tenant_id)


@router.post("/{action_id}/complete", response_model=CorrectiveAction)
async def complete_corrective_action(
    action_id: int,
    result_notes: Optional[str] = None,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Mark a corrective action as completed."""
    db_action = await crud_action.get_or_404(session, action_id, tenant_id)
    if db_action.completed:
        raise HTTPException(status_code=400, detail="Actie is al afgerond")

    updates = {
        "completed": True,
        "completed_date": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    if result_notes:
        updates["result_notes"] = result_notes

    return await crud_action.update(session, db_obj=db_action, obj_in=updates, tenant_id=tenant_id)


@router.post("/{action_id}/verify", response_model=CorrectiveAction)
async def verify_corrective_action(
    action_id: int,
    verified_by_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Verify a completed corrective action."""
    db_action = await crud_action.get_or_404(session, action_id, tenant_id)
    if not db_action.completed:
        raise HTTPException(status_code=400, detail="Actie moet eerst afgerond zijn voordat deze geverifieerd kan worden")

    return await crud_action.update(session, db_obj=db_action, obj_in={
        "verified": True,
        "verified_by_id": verified_by_id,
        "updated_at": datetime.utcnow(),
    }, tenant_id=tenant_id)


@router.delete("/{action_id}")
async def delete_corrective_action(
    action_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Delete a corrective action."""
    await crud_action.get_or_404(session, action_id, tenant_id)
    deleted = await crud_action.delete(session, id=action_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return {"message": "Verbeteractie verwijderd"}
