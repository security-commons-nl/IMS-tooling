"""
Measure Catalog Endpoints
Handles the catalog/library of reusable, generic measures (maatregelen).

Measures are normative building blocks that define WHAT should be done.
Controls are the context-specific implementations that define HOW it's done.
"""
from typing import List, Optional
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import CRUDBase
from app.core.rbac import require_editor, get_tenant_id
from app.models.core_models import (
    Measure,
    ControlMeasureLink,
    Control,
    User,
)
from app.services.knowledge_service import knowledge_service

router = APIRouter()
crud_measure = CRUDBase(Measure)
logger = logging.getLogger(__name__)


# =============================================================================
# MEASURE CATALOG CRUD
# =============================================================================

@router.get("/", response_model=List[Measure])
async def list_measures(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by measure category"),
    control_type: Optional[str] = Query(None, description="Filter by control type"),
    is_active: bool = Query(True, description="Filter by active status"),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """
    List measures from the catalog.

    Returns both global measures (tenant_id=NULL) and tenant-specific measures.
    """
    from sqlalchemy import or_

    query = select(Measure).where(
        Measure.is_active == is_active,
        or_(
            Measure.tenant_id == tenant_id,
            Measure.tenant_id.is_(None),
        ),
    )

    if category:
        query = query.where(Measure.measure_category == category)
    if control_type:
        query = query.where(Measure.control_type == control_type)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.get("/global", response_model=List[Measure])
async def list_global_measures(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by measure category"),
    session: AsyncSession = Depends(get_session),
):
    """List only global measures (tenant_id=NULL) available to all tenants."""
    query = select(Measure).where(
        Measure.tenant_id.is_(None),
        Measure.is_active == True
    )

    if category:
        query = query.where(Measure.measure_category == category)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/", response_model=Measure)
async def create_measure(
    measure: Measure,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """
    Create a new measure in the catalog.

    Set tenant_id=NULL in the body to create a global measure available to all tenants.
    Otherwise, tenant_id is enforced from the authenticated context.
    """
    # Only set tenant_id if not explicitly set to None (global measure)
    if measure.tenant_id is not None:
        measure.tenant_id = tenant_id
    created_measure = await crud_measure.create(session, obj_in=measure)

    # Index in knowledge base for AI RAG
    try:
        content = f"Maatregel: {created_measure.name}\n\nBeschrijving: {created_measure.description or ''}\n\nImplementatie richtlijn: {created_measure.implementation_guidance or ''}"
        await knowledge_service.add_knowledge(
            session=session,
            key=f"measure_catalog_{created_measure.id}",
            title=created_measure.name or f"Measure {created_measure.id}",
            content=content,
            category="measure_catalog"
        )
    except Exception as e:
        logger.warning(f"Failed to index measure {created_measure.id} in knowledge base: {e}")

    return created_measure


@router.get("/{measure_id}", response_model=Measure)
async def get_measure(
    measure_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a measure from the catalog by ID (must be global or belong to tenant)."""
    from sqlalchemy import or_
    result = await session.execute(
        select(Measure).where(
            Measure.id == measure_id,
            or_(
                Measure.tenant_id == tenant_id,
                Measure.tenant_id.is_(None),
            ),
        )
    )
    obj = result.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail=f"Measure with id {measure_id} not found")
    return obj


@router.patch("/{measure_id}", response_model=Measure)
async def update_measure(
    measure_id: int,
    measure_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """Update a measure in the catalog (only tenant-owned or global)."""
    from sqlalchemy import or_
    result = await session.execute(
        select(Measure).where(
            Measure.id == measure_id,
            or_(
                Measure.tenant_id == tenant_id,
                Measure.tenant_id.is_(None),
            ),
        )
    )
    db_measure = result.scalars().first()
    if not db_measure:
        raise HTTPException(status_code=404, detail=f"Measure with id {measure_id} not found")
    # Prevent changing tenant_id
    measure_update.pop("tenant_id", None)
    return await crud_measure.update(session, db_obj=db_measure, obj_in=measure_update)


@router.delete("/{measure_id}")
async def delete_measure(
    measure_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_editor),
):
    """
    Soft-delete a measure from the catalog.

    Sets is_active=False rather than hard delete to preserve references.
    """
    db_measure = await crud_measure.get_or_404(session, measure_id)
    await crud_measure.update(session, db_obj=db_measure, obj_in={"is_active": False})
    return {"message": "Measure deactivated"}


# =============================================================================
# MEASURE-CONTROL LINKAGE (Which controls implement this measure?)
# =============================================================================

@router.get("/{measure_id}/controls", response_model=List[Control])
async def get_implementing_controls(
    measure_id: int,
    _tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = _tenant_id
    """
    Get all controls that implement this measure.

    Shows where and how this catalog measure is actually implemented
    across different contexts (scopes, tenants).
    """
    await crud_measure.get_or_404(session, measure_id)

    query = (
        select(Control)
        .join(ControlMeasureLink, ControlMeasureLink.control_id == Control.id)
        .where(ControlMeasureLink.measure_id == measure_id)
    )

    if tenant_id:
        query = query.where(Control.tenant_id == tenant_id)

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/{measure_id}/coverage")
async def get_measure_coverage(
    measure_id: int,
    _tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = _tenant_id
    """
    Get coverage statistics for this measure.

    Shows how many controls implement this measure and their effectiveness.
    """
    from sqlalchemy import func

    await crud_measure.get_or_404(session, measure_id)

    query = (
        select(
            func.count(Control.id).label("control_count"),
            func.avg(Control.effectiveness_percentage).label("avg_effectiveness"),
        )
        .join(ControlMeasureLink, ControlMeasureLink.control_id == Control.id)
        .where(ControlMeasureLink.measure_id == measure_id)
    )

    if tenant_id:
        query = query.where(Control.tenant_id == tenant_id)

    result = await session.execute(query)
    row = result.first()

    return {
        "measure_id": measure_id,
        "implementing_controls": row.control_count or 0,
        "average_effectiveness": round(row.avg_effectiveness, 1) if row.avg_effectiveness else None,
    }


# =============================================================================
# MEASURE CATEGORIES
# =============================================================================

@router.get("/categories/list")
async def list_categories(
    session: AsyncSession = Depends(get_session),
):
    """Get all unique measure categories in the catalog."""
    from sqlalchemy import func, distinct

    result = await session.execute(
        select(distinct(Measure.measure_category))
        .where(
            Measure.measure_category.isnot(None),
            Measure.is_active == True
        )
    )
    categories = [row[0] for row in result if row[0]]
    return {"categories": sorted(categories)}


@router.get("/categories/{category}", response_model=List[Measure])
async def get_measures_by_category(
    category: str,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get all measures in a specific category."""
    result = await session.execute(
        select(Measure)
        .where(
            Measure.measure_category == category,
            Measure.is_active == True
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# =============================================================================
# MEASURE STATISTICS
# =============================================================================

@router.get("/stats/summary")
async def get_catalog_stats(
    tenant_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get summary statistics for the measure catalog."""
    from sqlalchemy import func

    # Base query for active measures
    base_query = select(func.count(Measure.id)).where(Measure.is_active == True)

    if tenant_id:
        # Count tenant-specific + global measures
        total_result = await session.execute(
            base_query.where(
                (Measure.tenant_id == tenant_id) | (Measure.tenant_id.is_(None))
            )
        )
    else:
        total_result = await session.execute(base_query)

    total = total_result.scalar() or 0

    # Count by category
    category_query = (
        select(
            Measure.measure_category,
            func.count(Measure.id).label("count")
        )
        .where(Measure.is_active == True)
        .group_by(Measure.measure_category)
    )

    if tenant_id:
        category_query = category_query.where(
            (Measure.tenant_id == tenant_id) | (Measure.tenant_id.is_(None))
        )

    category_result = await session.execute(category_query)
    by_category = {row.measure_category or "Uncategorized": row.count for row in category_result}

    return {
        "total_measures": total,
        "by_category": by_category,
    }
