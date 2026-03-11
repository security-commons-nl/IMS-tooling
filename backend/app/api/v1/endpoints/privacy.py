"""
Privacy (PIMS/AVG) Endpoints
Handles Processing Activities, Data Subject Requests, and Processor Agreements.
Implements GDPR/AVG compliance tracking.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import ScopedTenantCRUDBase, TenantCRUDBase
from app.core.rbac import get_tenant_id, get_scope_access
from app.models.core_models import (
    ProcessingActivity,
    DataSubjectRequest,
    ProcessorAgreement,
    LegalBasis,
    DataSubjectRequestType,
    Status,
)

router = APIRouter()
crud_processing = ScopedTenantCRUDBase(ProcessingActivity)
crud_dsr = TenantCRUDBase(DataSubjectRequest)
crud_processor = TenantCRUDBase(ProcessorAgreement)


# =============================================================================
# PROCESSING ACTIVITIES (Art. 30 Register)
# =============================================================================

@router.get("/processing-activities/", response_model=List[ProcessingActivity])
async def list_processing_activities(
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = Depends(get_tenant_id),
    accessible_scopes: set[int] | None = Depends(get_scope_access),
    scope_id: Optional[int] = Query(None),
    legal_basis: Optional[LegalBasis] = Query(None),
    is_active: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """List processing activities (Art. 30 register)."""
    filters = {}
    if scope_id:
        filters["scope_id"] = scope_id
    if is_active:
        filters["status"] = Status.ACTIVE

    return await crud_processing.get_multi_scoped(
        session, tenant_id, accessible_scopes,
        skip=skip, limit=limit, filters=filters,
    )


@router.post("/processing-activities/", response_model=ProcessingActivity)
async def create_processing_activity(
    activity: ProcessingActivity,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Create a new processing activity."""
    return await crud_processing.create(session, obj_in=activity, tenant_id=tenant_id)


@router.get("/processing-activities/{activity_id}", response_model=ProcessingActivity)
async def get_processing_activity(
    activity_id: int,
    tenant_id: int = Depends(get_tenant_id),
    accessible_scopes: set[int] | None = Depends(get_scope_access),
    session: AsyncSession = Depends(get_session),
):
    """Get a processing activity by ID."""
    return await crud_processing.get_scoped_or_404(session, activity_id, tenant_id, accessible_scopes)


@router.patch("/processing-activities/{activity_id}", response_model=ProcessingActivity)
async def update_processing_activity(
    activity_id: int,
    activity_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    accessible_scopes: set[int] | None = Depends(get_scope_access),
    session: AsyncSession = Depends(get_session),
):
    """Update a processing activity."""
    db_activity = await crud_processing.get_scoped_or_404(session, activity_id, tenant_id, accessible_scopes)
    activity_update["updated_at"] = datetime.utcnow()
    return await crud_processing.update(session, db_obj=db_activity, obj_in=activity_update, tenant_id=tenant_id)


@router.delete("/processing-activities/{activity_id}")
async def delete_processing_activity(
    activity_id: int,
    tenant_id: int = Depends(get_tenant_id),
    accessible_scopes: set[int] | None = Depends(get_scope_access),
    session: AsyncSession = Depends(get_session),
):
    """Delete a processing activity."""
    await crud_processing.get_scoped_or_404(session, activity_id, tenant_id, accessible_scopes)
    deleted = await crud_processing.delete(session, id=activity_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Processing activity not found")
    return {"message": "Processing activity deleted"}


@router.get("/processing-activities/requiring-dpia", response_model=List[ProcessingActivity])
async def get_activities_requiring_dpia(
    tenant_id: int = Depends(get_tenant_id),
    accessible_scopes: set[int] | None = Depends(get_scope_access),
    session: AsyncSession = Depends(get_session),
):
    """Get processing activities that may require a DPIA."""
    query = select(ProcessingActivity).where(
        ProcessingActivity.tenant_id == tenant_id,
        ProcessingActivity.status == Status.ACTIVE,
        ProcessingActivity.dpia_required == True,
    )

    # Apply scope filtering
    if accessible_scopes is not None:
        query = query.where(
            or_(
                ProcessingActivity.scope_id.in_(accessible_scopes),
                ProcessingActivity.scope_id.is_(None),
            )
        )

    result = await session.execute(query)
    return result.scalars().all()


# =============================================================================
# DATA SUBJECT REQUESTS (Art. 15-22)
# =============================================================================

@router.get("/data-subject-requests/", response_model=List[DataSubjectRequest])
async def list_data_subject_requests(
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = Depends(get_tenant_id),
    request_type: Optional[DataSubjectRequestType] = Query(None),
    status: Optional[Status] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List data subject requests."""
    query = select(DataSubjectRequest).where(DataSubjectRequest.tenant_id == tenant_id)

    if request_type:
        query = query.where(DataSubjectRequest.request_type == request_type)
    if status:
        query = query.where(DataSubjectRequest.status == status)

    query = query.order_by(DataSubjectRequest.received_date.desc())
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/data-subject-requests/", response_model=DataSubjectRequest)
async def create_data_subject_request(
    request: DataSubjectRequest,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Create a new data subject request."""
    # Set deadline (30 days by default per GDPR)
    if request.deadline is None:
        request.deadline = datetime.utcnow() + timedelta(days=30)

    request.status = Status.ACTIVE
    return await crud_dsr.create(session, obj_in=request, tenant_id=tenant_id)


@router.get("/data-subject-requests/{request_id}", response_model=DataSubjectRequest)
async def get_data_subject_request(
    request_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a data subject request by ID."""
    return await crud_dsr.get_or_404(session, request_id, tenant_id)


@router.patch("/data-subject-requests/{request_id}", response_model=DataSubjectRequest)
async def update_data_subject_request(
    request_id: int,
    request_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Update a data subject request."""
    db_request = await crud_dsr.get_or_404(session, request_id, tenant_id)
    request_update["updated_at"] = datetime.utcnow()
    return await crud_dsr.update(session, db_obj=db_request, obj_in=request_update, tenant_id=tenant_id)


@router.post("/data-subject-requests/{request_id}/complete", response_model=DataSubjectRequest)
async def complete_data_subject_request(
    request_id: int,
    completed_by_id: int,
    response_notes: Optional[str] = None,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Mark a data subject request as completed."""
    db_request = await crud_dsr.get_or_404(session, request_id, tenant_id)

    return await crud_dsr.update(session, db_obj=db_request, obj_in={
        "status": Status.CLOSED,
        "completed_at": datetime.utcnow(),
        "completed_by_id": completed_by_id,
        "response_notes": response_notes,
    }, tenant_id=tenant_id)


@router.post("/data-subject-requests/{request_id}/extend-deadline", response_model=DataSubjectRequest)
async def extend_deadline(
    request_id: int,
    new_deadline: datetime,
    extension_reason: str,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Extend the deadline for a data subject request (max 2 months per GDPR)."""
    db_request = await crud_dsr.get_or_404(session, request_id, tenant_id)

    # Validate extension is within GDPR limits (2 months max extension)
    original_deadline = db_request.deadline or db_request.created_at + timedelta(days=30)
    max_deadline = original_deadline + timedelta(days=60)

    if new_deadline > max_deadline:
        raise HTTPException(
            status_code=400,
            detail="Extension exceeds maximum allowed (2 months)"
        )

    return await crud_dsr.update(session, db_obj=db_request, obj_in={
        "deadline": new_deadline,
        "extension_reason": extension_reason,
        "updated_at": datetime.utcnow(),
    }, tenant_id=tenant_id)


@router.get("/data-subject-requests/overdue", response_model=List[DataSubjectRequest])
async def get_overdue_requests(
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get data subject requests that have exceeded their deadline."""
    query = select(DataSubjectRequest).where(
        DataSubjectRequest.tenant_id == tenant_id,
        DataSubjectRequest.status == Status.ACTIVE,
        DataSubjectRequest.deadline < datetime.utcnow(),
    )

    result = await session.execute(query)
    return result.scalars().all()


@router.get("/data-subject-requests/due-soon", response_model=List[DataSubjectRequest])
async def get_requests_due_soon(
    days: int = Query(7, ge=1, le=30),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get data subject requests due within specified days."""
    now = datetime.utcnow()
    deadline = now + timedelta(days=days)

    query = select(DataSubjectRequest).where(
        DataSubjectRequest.tenant_id == tenant_id,
        DataSubjectRequest.status == Status.ACTIVE,
        DataSubjectRequest.deadline >= now,
        DataSubjectRequest.deadline <= deadline,
    )

    result = await session.execute(query)
    return result.scalars().all()


# =============================================================================
# PROCESSOR AGREEMENTS (Art. 28)
# =============================================================================

@router.get("/processor-agreements/", response_model=List[ProcessorAgreement])
async def list_processor_agreements(
    skip: int = 0,
    limit: int = 100,
    tenant_id: int = Depends(get_tenant_id),
    supplier_id: Optional[int] = Query(None),
    is_active: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """List processor agreements."""
    query = select(ProcessorAgreement).where(ProcessorAgreement.tenant_id == tenant_id)

    if supplier_id:
        query = query.where(ProcessorAgreement.supplier_id == supplier_id)
    if is_active:
        query = query.where(ProcessorAgreement.status == Status.ACTIVE)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/processor-agreements/", response_model=ProcessorAgreement)
async def create_processor_agreement(
    agreement: ProcessorAgreement,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Create a new processor agreement."""
    return await crud_processor.create(session, obj_in=agreement, tenant_id=tenant_id)


@router.get("/processor-agreements/{agreement_id}", response_model=ProcessorAgreement)
async def get_processor_agreement(
    agreement_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get a processor agreement by ID."""
    return await crud_processor.get_or_404(session, agreement_id, tenant_id)


@router.patch("/processor-agreements/{agreement_id}", response_model=ProcessorAgreement)
async def update_processor_agreement(
    agreement_id: int,
    agreement_update: dict,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Update a processor agreement."""
    db_agreement = await crud_processor.get_or_404(session, agreement_id, tenant_id)
    agreement_update["updated_at"] = datetime.utcnow()
    return await crud_processor.update(session, db_obj=db_agreement, obj_in=agreement_update, tenant_id=tenant_id)


@router.delete("/processor-agreements/{agreement_id}")
async def delete_processor_agreement(
    agreement_id: int,
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Delete a processor agreement."""
    deleted = await crud_processor.delete(session, id=agreement_id, tenant_id=tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Processor agreement not found")
    return {"message": "Processor agreement deleted"}


@router.get("/processor-agreements/expiring-soon", response_model=List[ProcessorAgreement])
async def get_expiring_agreements(
    days: int = Query(90, ge=1, le=365),
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get processor agreements expiring within specified days."""
    now = datetime.utcnow()
    deadline = now + timedelta(days=days)

    query = select(ProcessorAgreement).where(
        ProcessorAgreement.tenant_id == tenant_id,
        ProcessorAgreement.status == Status.ACTIVE,
        ProcessorAgreement.end_date != None,
        ProcessorAgreement.end_date <= deadline,
    )

    result = await session.execute(query)
    return result.scalars().all()


# =============================================================================
# PRIVACY DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=dict)
async def get_privacy_dashboard(
    tenant_id: int = Depends(get_tenant_id),
    session: AsyncSession = Depends(get_session),
):
    """Get privacy compliance dashboard summary."""
    # Processing activities
    pa_query = select(ProcessingActivity).where(ProcessingActivity.tenant_id == tenant_id)
    pa_result = await session.execute(pa_query)
    activities = pa_result.scalars().all()

    # Data subject requests
    dsr_query = select(DataSubjectRequest).where(DataSubjectRequest.tenant_id == tenant_id)
    dsr_result = await session.execute(dsr_query)
    requests = dsr_result.scalars().all()

    # Processor agreements
    proc_query = select(ProcessorAgreement).where(ProcessorAgreement.tenant_id == tenant_id)
    proc_result = await session.execute(proc_query)
    agreements = proc_result.scalars().all()

    # Calculate stats
    open_dsrs = sum(1 for r in requests if r.status == Status.ACTIVE)
    overdue_dsrs = sum(1 for r in requests if r.status == Status.ACTIVE and r.deadline and r.deadline < datetime.utcnow())
    dpia_required = sum(1 for a in activities if a.dpia_required)

    return {
        "processing_activities": {
            "total": len(activities),
            "active": sum(1 for a in activities if a.status == Status.ACTIVE),
            "dpia_required": dpia_required,
        },
        "data_subject_requests": {
            "total": len(requests),
            "open": open_dsrs,
            "overdue": overdue_dsrs,
            "completed": sum(1 for r in requests if r.status == Status.CLOSED),
        },
        "processor_agreements": {
            "total": len(agreements),
            "active": sum(1 for a in agreements if a.status == Status.ACTIVE),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
