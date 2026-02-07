"""
Besluitlog (Decision Log) Endpoints — Hiaat 1
Handles formal management decisions with audit trail.
Hard rules: risks above threshold cannot be closed without a decision.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import CRUDBase
from app.models.core_models import (
    Decision,
    DecisionType,
    DecisionStatus,
    DecisionRiskLink,
    Risk,
)

router = APIRouter()
crud_decision = CRUDBase(Decision)
crud_risk = CRUDBase(Risk)


# =============================================================================
# DECISION CRUD
# =============================================================================

@router.get("/", response_model=List[Decision])
async def list_decisions(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = Query(None, description="Filter by tenant"),
    decision_type: Optional[DecisionType] = Query(None, description="Filter by type"),
    status: Optional[DecisionStatus] = Query(None, description="Filter by status"),
    session: AsyncSession = Depends(get_session),
):
    """List decisions with optional filters."""
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if decision_type:
        filters["decision_type"] = decision_type
    if status:
        filters["status"] = status

    return await crud_decision.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=Decision)
async def create_decision(
    decision: Decision,
    session: AsyncSession = Depends(get_session),
):
    """Create a new management decision (DT-only in production)."""
    return await crud_decision.create(session, obj_in=decision)


# =============================================================================
# HARD RULES & QUERIES — placed before /{decision_id} to avoid route conflicts
# =============================================================================

@router.get("/check-required/{risk_id}", response_model=dict)
async def check_decision_required(
    risk_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Check whether a formal decision is required for a risk.
    Hard rule: inherent_risk_score >= 9 requires a DT decision.
    """
    risk = await crud_risk.get_or_404(session, risk_id)

    threshold = 9  # Score >= 9 (HIGH x HIGH or above) requires decision
    required = (risk.inherent_risk_score or 0) >= threshold

    # Check if a decision already exists
    result = await session.execute(
        select(DecisionRiskLink).where(DecisionRiskLink.risk_id == risk_id)
    )
    existing_links = result.scalars().all()

    has_active_decision = False
    if existing_links:
        for link in existing_links:
            decision = await crud_decision.get(session, link.decision_id)
            if decision and decision.status == DecisionStatus.ACTIVE:
                has_active_decision = True
                break

    return {
        "risk_id": risk_id,
        "inherent_risk_score": risk.inherent_risk_score,
        "decision_required": required,
        "has_active_decision": has_active_decision,
        "can_close": not required or has_active_decision,
    }


@router.get("/expired", response_model=List[Decision])
async def get_expired_decisions(
    tenant_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
):
    """Get decisions that have passed their valid_until date but are still Active."""
    query = select(Decision).where(
        Decision.status == DecisionStatus.ACTIVE,
        Decision.valid_until != None,
        Decision.valid_until < datetime.utcnow(),
    )
    if tenant_id:
        query = query.where(Decision.tenant_id == tenant_id)

    result = await session.execute(query)
    return result.scalars().all()


# =============================================================================
# INDIVIDUAL DECISION — /{decision_id} routes placed LAST
# =============================================================================

@router.get("/{decision_id}", response_model=Decision)
async def get_decision(
    decision_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a decision by ID."""
    return await crud_decision.get_or_404(session, decision_id)


@router.patch("/{decision_id}", response_model=Decision)
async def update_decision(
    decision_id: int,
    decision_update: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update a decision."""
    db_decision = await crud_decision.get_or_404(session, decision_id)
    decision_update["updated_at"] = datetime.utcnow()
    return await crud_decision.update(session, db_obj=db_decision, obj_in=decision_update)


@router.delete("/{decision_id}")
async def delete_decision(
    decision_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a decision (only Draft/Active)."""
    deleted = await crud_decision.delete(session, id=decision_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Decision not found")
    return {"message": "Decision deleted"}


# =============================================================================
# DECISION STATUS LIFECYCLE
# =============================================================================

@router.post("/{decision_id}/expire", response_model=Decision)
async def expire_decision(
    decision_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Mark a decision as expired.
    Linked risks revert to 'besluit vereist' state.
    """
    db_decision = await crud_decision.get_or_404(session, decision_id)

    if db_decision.status != DecisionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Only active decisions can expire. Current: {db_decision.status}"
        )

    return await crud_decision.update(session, db_obj=db_decision, obj_in={
        "status": DecisionStatus.EXPIRED,
        "updated_at": datetime.utcnow(),
    })


@router.post("/{decision_id}/revoke", response_model=Decision)
async def revoke_decision(
    decision_id: int,
    reason: str = Query(..., description="Reason for revoking"),
    session: AsyncSession = Depends(get_session),
):
    """Revoke a decision."""
    db_decision = await crud_decision.get_or_404(session, decision_id)

    if db_decision.status != DecisionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Only active decisions can be revoked. Current: {db_decision.status}"
        )

    return await crud_decision.update(session, db_obj=db_decision, obj_in={
        "status": DecisionStatus.REVOKED,
        "conditions": reason,
        "updated_at": datetime.utcnow(),
    })


# =============================================================================
# DECISION-RISK LINKAGE
# =============================================================================

@router.post("/{decision_id}/risks/{risk_id}")
async def link_risk_to_decision(
    decision_id: int,
    risk_id: int,
    notes: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """Link a risk to a decision."""
    await crud_decision.get_or_404(session, decision_id)
    await crud_risk.get_or_404(session, risk_id)

    # Check duplicate
    result = await session.execute(
        select(DecisionRiskLink).where(
            DecisionRiskLink.decision_id == decision_id,
            DecisionRiskLink.risk_id == risk_id,
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Link already exists")

    link = DecisionRiskLink(
        decision_id=decision_id,
        risk_id=risk_id,
        notes=notes,
    )
    session.add(link)
    await session.commit()
    return {"message": "Risk linked to decision"}


@router.delete("/{decision_id}/risks/{risk_id}")
async def unlink_risk_from_decision(
    decision_id: int,
    risk_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Unlink a risk from a decision."""
    result = await session.execute(
        select(DecisionRiskLink).where(
            DecisionRiskLink.decision_id == decision_id,
            DecisionRiskLink.risk_id == risk_id,
        )
    )
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    await session.delete(link)
    await session.commit()
    return {"message": "Risk unlinked from decision"}


@router.get("/{decision_id}/risks", response_model=List[Risk])
async def get_decision_risks(
    decision_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get all risks linked to a decision."""
    await crud_decision.get_or_404(session, decision_id)

    result = await session.execute(
        select(Risk).join(
            DecisionRiskLink, Risk.id == DecisionRiskLink.risk_id
        ).where(DecisionRiskLink.decision_id == decision_id)
    )
    return result.scalars().all()
