"""
Policy Principles (Beleid-trace) Endpoints — Hiaat 6
Manages policy principles for traceability: Policy → Principle → Risk → Control.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import TenantCRUDBase
from app.core.rbac import require_configurer, get_tenant_id
from app.models.core_models import (
    PolicyPrinciple,
    Policy,
    Risk,
    Control,
    ControlRiskLink,
    User,
)

router = APIRouter()
crud_principle = TenantCRUDBase(PolicyPrinciple)
crud_policy = TenantCRUDBase(Policy)
crud_risk = TenantCRUDBase(Risk)


# =============================================================================
# PRINCIPLE CRUD
# =============================================================================

@router.get("/", response_model=List[PolicyPrinciple])
async def list_principles(
    skip: int = 0,
    limit: int = 100,
    policy_id: Optional[int] = Query(None),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """List policy principles."""
    filters = {}
    if policy_id:
        filters["policy_id"] = policy_id

    return await crud_principle.get_multi(session, tenant_id, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=PolicyPrinciple)
async def create_principle(
    principle: PolicyPrinciple,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Create a new policy principle."""
    # Verify policy exists within tenant
    await crud_policy.get_or_404(session, principle.policy_id, tenant_id)
    return await crud_principle.create(session, obj_in=principle, tenant_id=tenant_id)


# =============================================================================
# TRACE VIEW — placed before /{principle_id} to avoid route conflicts
# =============================================================================

@router.get("/trace/{control_id}", response_model=dict)
async def trace_control_origin(
    control_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Trace the full chain: Control <- Risk <- PolicyPrinciple <- Policy.
    Answers: "Why does this control exist?"
    """
    # Get control
    from app.core.crud import TenantCRUDBase
    from app.models.core_models import Control
    crud_control = TenantCRUDBase(Control)
    control = await crud_control.get_or_404(session, control_id, tenant_id)

    # Get linked risks
    result = await session.execute(
        select(Risk).join(
            ControlRiskLink, Risk.id == ControlRiskLink.risk_id
        ).where(ControlRiskLink.control_id == control_id)
    )
    risks = result.scalars().all()

    trace_chains = []
    for risk in risks:
        chain = {
            "risk_id": risk.id,
            "risk_title": risk.title,
            "principle": None,
            "policy": None,
        }

        # Check if risk links to a policy principle
        if risk.policy_principle_id:
            principle = await crud_principle.get(session, risk.policy_principle_id)
            if principle:
                chain["principle"] = {
                    "id": principle.id,
                    "code": principle.code,
                    "title": principle.title,
                }

                # Get the policy
                policy = await crud_policy.get(session, principle.policy_id)
                if policy:
                    chain["policy"] = {
                        "id": policy.id,
                        "title": policy.title,
                        "state": policy.state.value if policy.state else None,
                    }

        trace_chains.append(chain)

    return {
        "control_id": control.id,
        "control_title": control.title,
        "trace_chains": trace_chains,
    }


# =============================================================================
# INDIVIDUAL PRINCIPLE — /{principle_id} routes placed LAST
# =============================================================================

@router.get("/{principle_id}", response_model=PolicyPrinciple)
async def get_principle(
    principle_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a principle by ID."""
    return await crud_principle.get_or_404(session, principle_id, tenant_id)


@router.patch("/{principle_id}", response_model=PolicyPrinciple)
async def update_principle(
    principle_id: int,
    principle_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Update a principle."""
    db_principle = await crud_principle.get_or_404(session, principle_id, tenant_id)
    principle_update["updated_at"] = datetime.utcnow()
    return await crud_principle.update(session, db_obj=db_principle, obj_in=principle_update, tenant_id=tenant_id)


@router.delete("/{principle_id}")
async def delete_principle(
    principle_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Delete a principle."""
    await crud_principle.get_or_404(session, principle_id, tenant_id)
    deleted = await crud_principle.delete(session, id=principle_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Principle not found")
    return {"message": "Principle deleted"}
