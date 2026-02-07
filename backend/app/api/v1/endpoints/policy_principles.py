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
from app.core.crud import CRUDBase
from app.core.rbac import require_configurer
from app.models.core_models import (
    PolicyPrinciple,
    Policy,
    Risk,
    Control,
    ControlRiskLink,
    User,
)

router = APIRouter()
crud_principle = CRUDBase(PolicyPrinciple)
crud_policy = CRUDBase(Policy)
crud_risk = CRUDBase(Risk)


# =============================================================================
# PRINCIPLE CRUD
# =============================================================================

@router.get("/", response_model=List[PolicyPrinciple])
async def list_principles(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = Query(None),
    policy_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List policy principles."""
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if policy_id:
        filters["policy_id"] = policy_id

    return await crud_principle.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=PolicyPrinciple)
async def create_principle(
    principle: PolicyPrinciple,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Create a new policy principle."""
    # Verify policy exists
    await crud_policy.get_or_404(session, principle.policy_id)
    return await crud_principle.create(session, obj_in=principle)


# =============================================================================
# TRACE VIEW — placed before /{principle_id} to avoid route conflicts
# =============================================================================

@router.get("/trace/{control_id}", response_model=dict)
async def trace_control_origin(
    control_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Trace the full chain: Control <- Risk <- PolicyPrinciple <- Policy.
    Answers: "Why does this control exist?"
    """
    # Get control
    from app.core.crud import CRUDBase
    from app.models.core_models import Control
    crud_control = CRUDBase(Control)
    control = await crud_control.get_or_404(session, control_id)

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
    session: AsyncSession = Depends(get_session),
):
    """Get a principle by ID."""
    return await crud_principle.get_or_404(session, principle_id)


@router.patch("/{principle_id}", response_model=PolicyPrinciple)
async def update_principle(
    principle_id: int,
    principle_update: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Update a principle."""
    db_principle = await crud_principle.get_or_404(session, principle_id)
    principle_update["updated_at"] = datetime.utcnow()
    return await crud_principle.update(session, db_obj=db_principle, obj_in=principle_update)


@router.delete("/{principle_id}")
async def delete_principle(
    principle_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Delete a principle."""
    deleted = await crud_principle.delete(session, id=principle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Principle not found")
    return {"message": "Principle deleted"}
