"""
Measure Management Endpoints
Handles security/compliance measures (controls) with effectiveness tracking.
"""
from typing import List, Optional
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import CRUDBase
from app.models.core_models import (
    Measure,
    MeasureRiskLink,
    MeasureRequirementLink,
    Risk,
    Requirement,
    Status,
)
from app.services.knowledge_service import knowledge_service

router = APIRouter()
crud_measure = CRUDBase(Measure)
logger = logging.getLogger(__name__)


# =============================================================================
# MEASURE CRUD
# =============================================================================

@router.get("/", response_model=List[Measure])
async def list_measures(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = Query(None, description="Filter by tenant"),
    scope_id: Optional[int] = Query(None, description="Filter by scope"),
    status: Optional[Status] = Query(None, description="Filter by status"),
    owner_id: Optional[int] = Query(None, description="Filter by owner"),
    session: AsyncSession = Depends(get_session),
):
    """List measures with optional filters."""
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if scope_id:
        filters["scope_id"] = scope_id
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id

    return await crud_measure.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=Measure)
async def create_measure(
    measure: Measure,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new measure (control).

    Also indexes in knowledge base for AI RAG.
    """
    measure.status = measure.status or Status.DRAFT
    created_measure = await crud_measure.create(session, obj_in=measure)

    # Index in knowledge base for AI RAG
    try:
        content = f"Maatregel: {created_measure.title}\n\nBeschrijving: {created_measure.description or ''}\n\nImplementatie: {created_measure.implementation_details or ''}"
        await knowledge_service.add_knowledge(
            session=session,
            key=f"measure_{created_measure.id}",
            title=created_measure.title or f"Measure {created_measure.id}",
            content=content,
            category="measure"
        )
    except Exception as e:
        logger.warning(f"Failed to index measure {created_measure.id} in knowledge base: {e}")

    return created_measure


@router.get("/{measure_id}", response_model=Measure)
async def get_measure(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a measure by ID."""
    return await crud_measure.get_or_404(session, measure_id)


@router.patch("/{measure_id}", response_model=Measure)
async def update_measure(
    measure_id: int,
    measure_update: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update a measure."""
    db_measure = await crud_measure.get_or_404(session, measure_id)
    measure_update["updated_at"] = datetime.utcnow()
    return await crud_measure.update(session, db_obj=db_measure, obj_in=measure_update)


@router.delete("/{measure_id}")
async def delete_measure(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Delete a measure."""
    deleted = await crud_measure.delete(session, id=measure_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Measure not found")
    return {"message": "Measure deleted"}


# =============================================================================
# MEASURE STATUS TRANSITIONS
# =============================================================================

@router.post("/{measure_id}/activate", response_model=Measure)
async def activate_measure(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Activate a draft measure."""
    db_measure = await crud_measure.get_or_404(session, measure_id)

    if db_measure.status != Status.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Only draft measures can be activated. Current status: {db_measure.status}"
        )

    return await crud_measure.update(session, db_obj=db_measure, obj_in={
        "status": Status.ACTIVE,
        "updated_at": datetime.utcnow(),
    })


@router.post("/{measure_id}/deactivate", response_model=Measure)
async def deactivate_measure(
    measure_id: int,
    reason: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Deactivate an active measure."""
    db_measure = await crud_measure.get_or_404(session, measure_id)

    if db_measure.status != Status.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Only active measures can be deactivated. Current status: {db_measure.status}"
        )

    return await crud_measure.update(session, db_obj=db_measure, obj_in={
        "status": Status.INACTIVE,
        "updated_at": datetime.utcnow(),
    })


# =============================================================================
# EFFECTIVENESS TRACKING
# =============================================================================

@router.patch("/{measure_id}/effectiveness", response_model=Measure)
async def update_effectiveness(
    measure_id: int,
    effectiveness_score: int = Query(..., ge=0, le=100, description="Effectiveness percentage (0-100)"),
    last_tested_at: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Update the effectiveness score of a measure.

    Effectiveness is typically assessed through:
    - Testing results
    - Audit findings
    - Incident analysis
    """
    db_measure = await crud_measure.get_or_404(session, measure_id)

    update_data = {
        "effectiveness_score": effectiveness_score,
        "updated_at": datetime.utcnow(),
    }
    if last_tested_at:
        update_data["last_tested_at"] = last_tested_at

    return await crud_measure.update(session, db_obj=db_measure, obj_in=update_data)


# =============================================================================
# MEASURE-RISK LINKAGE
# =============================================================================

@router.get("/{measure_id}/risks", response_model=List[Risk])
async def get_linked_risks(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get all risks that this measure addresses."""
    await crud_measure.get_or_404(session, measure_id)

    result = await session.execute(
        select(Risk)
        .join(MeasureRiskLink, MeasureRiskLink.risk_id == Risk.id)
        .where(MeasureRiskLink.measure_id == measure_id)
    )
    return result.scalars().all()


@router.post("/{measure_id}/risks/{risk_id}")
async def link_to_risk(
    measure_id: int,
    risk_id: int,
    effectiveness_contribution: int = Query(50, ge=0, le=100),
    session: AsyncSession = Depends(get_session),
):
    """Link this measure to a risk."""
    await crud_measure.get_or_404(session, measure_id)

    # Check if link exists
    result = await session.execute(
        select(MeasureRiskLink).where(
            MeasureRiskLink.measure_id == measure_id,
            MeasureRiskLink.risk_id == risk_id
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Link already exists")

    link = MeasureRiskLink(
        measure_id=measure_id,
        risk_id=risk_id,
        effectiveness_contribution=effectiveness_contribution,
    )
    session.add(link)
    await session.commit()

    return {"message": "Measure linked to risk"}


@router.delete("/{measure_id}/risks/{risk_id}")
async def unlink_from_risk(
    measure_id: int,
    risk_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove link between this measure and a risk."""
    result = await session.execute(
        select(MeasureRiskLink).where(
            MeasureRiskLink.measure_id == measure_id,
            MeasureRiskLink.risk_id == risk_id
        )
    )
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    await session.delete(link)
    await session.commit()

    return {"message": "Link removed"}


# =============================================================================
# MEASURE-REQUIREMENT LINKAGE
# =============================================================================

@router.get("/{measure_id}/requirements", response_model=List[Requirement])
async def get_linked_requirements(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get all requirements (controls) that this measure implements."""
    await crud_measure.get_or_404(session, measure_id)

    result = await session.execute(
        select(Requirement)
        .join(MeasureRequirementLink, MeasureRequirementLink.requirement_id == Requirement.id)
        .where(MeasureRequirementLink.measure_id == measure_id)
    )
    return result.scalars().all()


@router.post("/{measure_id}/requirements/{requirement_id}")
async def link_to_requirement(
    measure_id: int,
    requirement_id: int,
    implementation_status: str = Query("partial", regex="^(none|partial|full)$"),
    session: AsyncSession = Depends(get_session),
):
    """
    Link this measure to a requirement (control from a standard).

    This creates the mapping for Statement of Applicability (SoA).
    """
    await crud_measure.get_or_404(session, measure_id)

    # Check if link exists
    result = await session.execute(
        select(MeasureRequirementLink).where(
            MeasureRequirementLink.measure_id == measure_id,
            MeasureRequirementLink.requirement_id == requirement_id
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Link already exists")

    link = MeasureRequirementLink(
        measure_id=measure_id,
        requirement_id=requirement_id,
        implementation_status=implementation_status,
    )
    session.add(link)
    await session.commit()

    return {"message": "Measure linked to requirement"}


@router.delete("/{measure_id}/requirements/{requirement_id}")
async def unlink_from_requirement(
    measure_id: int,
    requirement_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove link between this measure and a requirement."""
    result = await session.execute(
        select(MeasureRequirementLink).where(
            MeasureRequirementLink.measure_id == measure_id,
            MeasureRequirementLink.requirement_id == requirement_id
        )
    )
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    await session.delete(link)
    await session.commit()

    return {"message": "Link removed"}


# =============================================================================
# MEASURE STATISTICS
# =============================================================================

@router.get("/stats/by-status")
async def get_measures_by_status(
    tenant_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get measure counts grouped by status."""
    from sqlalchemy import func

    query = select(
        Measure.status,
        func.count(Measure.id).label("count")
    ).group_by(Measure.status)

    if tenant_id:
        query = query.where(Measure.tenant_id == tenant_id)

    result = await session.execute(query)
    return {row.status: row.count for row in result}


@router.get("/stats/effectiveness")
async def get_effectiveness_stats(
    tenant_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get effectiveness statistics for measures."""
    from sqlalchemy import func

    query = select(
        func.avg(Measure.effectiveness_score).label("average"),
        func.min(Measure.effectiveness_score).label("minimum"),
        func.max(Measure.effectiveness_score).label("maximum"),
        func.count(Measure.id).label("total")
    ).where(Measure.effectiveness_score.isnot(None))

    if tenant_id:
        query = query.where(Measure.tenant_id == tenant_id)

    result = await session.execute(query)
    row = result.first()

    return {
        "average_effectiveness": round(row.average, 1) if row.average else 0,
        "min_effectiveness": row.minimum or 0,
        "max_effectiveness": row.maximum or 0,
        "measures_with_score": row.total or 0
    }
