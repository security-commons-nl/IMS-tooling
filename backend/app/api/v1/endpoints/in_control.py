"""
In-Control Status Endpoints — Hiaat 5
Calculates and manages in-control status per scope/domain.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import CRUDBase
from app.core.rbac import require_configurer
from app.models.core_models import (
    InControlAssessment,
    InControlLevel,
    RiskLevel,
    Risk,
    Control,
    Finding,
    CorrectiveAction,
    Assessment,
    Status,
    Scope,
    User,
)

router = APIRouter()
crud_assessment = CRUDBase(InControlAssessment)
crud_scope = CRUDBase(Scope)


# =============================================================================
# SHARED CALCULATION LOGIC
# =============================================================================

async def _calculate_scope_level(
    session: AsyncSession, scope_id: int, tenant_id: int
) -> dict:
    """Calculate in-control level for a single scope based on live data."""
    # Count open risks
    result = await session.execute(
        select(func.count()).select_from(Risk).where(
            Risk.scope_id == scope_id,
            Risk.tenant_id == tenant_id,
            Risk.status == Status.ACTIVE,
        )
    )
    open_risks = result.scalar() or 0

    # Count high/critical risks
    result = await session.execute(
        select(func.count()).select_from(Risk).where(
            Risk.scope_id == scope_id,
            Risk.tenant_id == tenant_id,
            Risk.status == Status.ACTIVE,
            Risk.inherent_impact.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
        )
    )
    high_risks = result.scalar() or 0

    # Count open findings (filtered by scope via assessment)
    result = await session.execute(
        select(func.count()).select_from(Finding).join(
            Assessment, Finding.assessment_id == Assessment.id
        ).where(
            Finding.tenant_id == tenant_id,
            Finding.status == Status.ACTIVE,
            Assessment.scope_id == scope_id,
        )
    )
    open_findings = result.scalar() or 0

    # Count overdue corrective actions (filtered by scope via finding -> assessment)
    result = await session.execute(
        select(func.count()).select_from(CorrectiveAction).join(
            Finding, CorrectiveAction.finding_id == Finding.id
        ).join(
            Assessment, Finding.assessment_id == Assessment.id
        ).where(
            CorrectiveAction.tenant_id == tenant_id,
            CorrectiveAction.completed == False,
            CorrectiveAction.due_date != None,
            CorrectiveAction.due_date < datetime.utcnow(),
            Assessment.scope_id == scope_id,
        )
    )
    overdue_actions = result.scalar() or 0

    # Count controls without test results
    result = await session.execute(
        select(func.count()).select_from(Control).where(
            Control.scope_id == scope_id,
            Control.tenant_id == tenant_id,
            Control.status == Status.ACTIVE,
            Control.last_tested == None,
        )
    )
    missing_controls = result.scalar() or 0

    # Determine level
    if high_risks > 0 or overdue_actions > 3 or open_findings > 5:
        level = InControlLevel.NOT_IN_CONTROL
    elif open_risks > 3 or overdue_actions > 0 or open_findings > 2:
        level = InControlLevel.LIMITED_CONTROL
    else:
        level = InControlLevel.IN_CONTROL

    return {
        "level": level,
        "open_risks_count": open_risks,
        "high_risks_count": high_risks,
        "missing_controls_count": missing_controls,
        "open_findings_count": open_findings,
        "overdue_actions_count": overdue_actions,
    }


# =============================================================================
# IN-CONTROL ASSESSMENTS
# =============================================================================

@router.get("/", response_model=List[InControlAssessment])
async def list_in_control_assessments(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = Query(None),
    scope_id: Optional[int] = Query(None),
    level: Optional[InControlLevel] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List in-control assessments."""
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if scope_id:
        filters["scope_id"] = scope_id
    if level:
        filters["level"] = level

    return await crud_assessment.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=InControlAssessment)
async def create_in_control_assessment(
    assessment: InControlAssessment,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Create a new in-control assessment."""
    return await crud_assessment.create(session, obj_in=assessment)


# =============================================================================
# CALCULATED STATUS — placed before /{assessment_id} to avoid route conflicts
# =============================================================================

@router.get("/calculate/{scope_id}", response_model=dict)
async def calculate_in_control_status(
    scope_id: int,
    tenant_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Calculate the in-control status for a scope based on current data.
    Returns the calculated level and supporting metrics.
    Does NOT save — use POST /in-control/ to formally record.
    """
    await crud_scope.get_or_404(session, scope_id)
    metrics = await _calculate_scope_level(session, scope_id, tenant_id)

    return {
        "scope_id": scope_id,
        "calculated_level": metrics["level"].value,
        "open_risks_count": metrics["open_risks_count"],
        "high_risks_count": metrics["high_risks_count"],
        "missing_controls_count": metrics["missing_controls_count"],
        "open_findings_count": metrics["open_findings_count"],
        "overdue_actions_count": metrics["overdue_actions_count"],
    }


# =============================================================================
# DASHBOARD DATA
# =============================================================================

@router.get("/dashboard", response_model=List[dict])
async def get_in_control_dashboard(
    tenant_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Get in-control overview for all scopes with live-calculated status.
    Falls back to stored assessment if calculation data is unavailable.
    For the DT dashboard.
    """
    # Get all active scopes for this tenant
    result = await session.execute(
        select(Scope).where(
            Scope.tenant_id == tenant_id,
            Scope.is_active == True,
        )
    )
    scopes = result.scalars().all()

    dashboard = []
    for scope in scopes:
        # Live-calculate the in-control level from current data
        metrics = await _calculate_scope_level(session, scope.id, tenant_id)

        # Get latest formal assessment for context (date, established status)
        result = await session.execute(
            select(InControlAssessment).where(
                InControlAssessment.scope_id == scope.id,
                InControlAssessment.tenant_id == tenant_id,
            ).order_by(InControlAssessment.assessment_date.desc()).limit(1)
        )
        latest = result.scalars().first()

        dashboard.append({
            "scope_id": scope.id,
            "scope_name": scope.name,
            "scope_type": scope.type.value if scope.type else None,
            "level": metrics["level"].value,
            "open_risks_count": metrics["open_risks_count"],
            "high_risks_count": metrics["high_risks_count"],
            "open_findings_count": metrics["open_findings_count"],
            "overdue_actions_count": metrics["overdue_actions_count"],
            "missing_controls_count": metrics["missing_controls_count"],
            "assessment_date": latest.assessment_date.isoformat() if latest else None,
            "established": latest.established_date is not None if latest else False,
        })

    return dashboard


# =============================================================================
# INDIVIDUAL ASSESSMENT — /{assessment_id} routes placed LAST to avoid conflicts
# =============================================================================

@router.get("/{assessment_id}", response_model=InControlAssessment)
async def get_in_control_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get an in-control assessment by ID."""
    return await crud_assessment.get_or_404(session, assessment_id)


@router.post("/{assessment_id}/establish", response_model=InControlAssessment)
async def establish_in_control(
    assessment_id: int,
    established_by_id: int = Query(..., description="DT user who establishes"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_configurer),
):
    """Formally establish an in-control status (DT-only)."""
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)
    return await crud_assessment.update(session, db_obj=db_assessment, obj_in={
        "established_by_id": established_by_id,
        "established_date": datetime.utcnow(),
    })
