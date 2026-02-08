"""
Assessment (Verification) Endpoints
Handles Assessments, Findings, Evidence, and Corrective Actions.
Implements the PDCA "Check" phase.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.core.crud import CRUDBase
from app.core.rbac import require_oversight
from app.models.core_models import (
    Assessment,
    AssessmentType,
    AssessmentPhase,
    AssessmentQuestion,
    AssessmentResponse,
    Finding,
    FindingSeverity,
    Evidence,
    CorrectiveAction,
    BIAThreshold,
    Scope,
    Status,
    AuditResult,
    ClassificationLevel,
    User,
)

router = APIRouter()
crud_assessment = CRUDBase(Assessment)
crud_finding = CRUDBase(Finding)
crud_evidence = CRUDBase(Evidence)
crud_corrective_action = CRUDBase(CorrectiveAction)
crud_question = CRUDBase(AssessmentQuestion)
crud_response = CRUDBase(AssessmentResponse)
crud_threshold = CRUDBase(BIAThreshold)


# =============================================================================
# ASSESSMENT CRUD
# =============================================================================

@router.get("/", response_model=List[Assessment])
async def list_assessments(
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[int] = Query(None),
    assessment_type: Optional[AssessmentType] = Query(None),
    status: Optional[Status] = Query(None),
    scope_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List assessments with optional filters."""
    filters = {}
    if tenant_id:
        filters["tenant_id"] = tenant_id
    if assessment_type:
        filters["type"] = assessment_type
    if status:
        filters["status"] = status
    if scope_id:
        filters["scope_id"] = scope_id

    return await crud_assessment.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/", response_model=Assessment)
async def create_assessment(
    assessment: Assessment,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Create a new assessment."""
    return await crud_assessment.create(session, obj_in=assessment)


# =============================================================================
# BIA THRESHOLDS (before /{assessment_id} routes)
# =============================================================================

@router.get("/bia-thresholds", response_model=List[BIAThreshold])
async def list_bia_thresholds(
    tenant_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Get BIA threshold configuration. Returns tenant-specific or global defaults."""
    if tenant_id:
        stmt = select(BIAThreshold).where(BIAThreshold.tenant_id == tenant_id).order_by(BIAThreshold.score)
        result = await session.execute(stmt)
        thresholds = result.scalars().all()
        if thresholds:
            return thresholds

    # Fall back to global defaults (tenant_id IS NULL)
    stmt = select(BIAThreshold).where(BIAThreshold.tenant_id == None).order_by(BIAThreshold.score)  # noqa: E711
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/bia-thresholds", response_model=BIAThreshold)
async def create_bia_threshold(
    threshold: BIAThreshold,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Create or update a BIA threshold entry."""
    return await crud_threshold.create(session, obj_in=threshold)


# =============================================================================
# ACT-FEEDBACKLOOP DASHBOARD (Hiaat 7) — placed before /{assessment_id} routes
# =============================================================================

@router.get("/act-overdue", response_model=dict)
async def get_act_overdue_summary(
    tenant_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Hiaat 7: Dashboard signal for overdue ACT items.
    Returns open findings that have incomplete corrective actions
    or no corrective actions at all.
    """
    # Get all open findings
    stmt = select(Finding).where(Finding.status != Status.CLOSED)
    if tenant_id:
        stmt = stmt.where(Finding.tenant_id == tenant_id)
    result = await session.execute(stmt)
    open_findings = result.scalars().all()

    blocked_findings = []
    no_action_findings = []

    for finding in open_findings:
        actions_result = await session.execute(
            select(CorrectiveAction).where(CorrectiveAction.finding_id == finding.id)
        )
        actions = actions_result.scalars().all()

        if not actions:
            no_action_findings.append({
                "finding_id": finding.id,
                "title": finding.title,
                "severity": finding.severity.value if finding.severity else None,
            })
        else:
            completed = [a for a in actions if a.status == Status.CLOSED]
            if not completed:
                overdue_actions = []
                for a in actions:
                    overdue_actions.append({
                        "action_id": a.id,
                        "description": a.description,
                        "due_date": str(a.due_date) if a.due_date else None,
                    })
                blocked_findings.append({
                    "finding_id": finding.id,
                    "title": finding.title,
                    "severity": finding.severity.value if finding.severity else None,
                    "pending_actions": overdue_actions,
                })

    return {
        "open_findings_count": len(open_findings),
        "blocked_count": len(blocked_findings),
        "no_action_count": len(no_action_findings),
        "blocked_findings": blocked_findings,
        "no_action_findings": no_action_findings,
    }


@router.get("/{assessment_id}", response_model=Assessment)
async def get_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get an assessment by ID."""
    return await crud_assessment.get_or_404(session, assessment_id)


@router.patch("/{assessment_id}", response_model=Assessment)
async def update_assessment(
    assessment_id: int,
    assessment_update: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Update an assessment."""
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)
    return await crud_assessment.update(session, db_obj=db_assessment, obj_in=assessment_update)


@router.delete("/{assessment_id}")
async def delete_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Delete an assessment."""
    deleted = await crud_assessment.delete(session, id=assessment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"message": "Assessment deleted"}


# =============================================================================
# ASSESSMENT LIFECYCLE & PHASE MANAGEMENT
# =============================================================================

@router.post("/{assessment_id}/advance-phase", response_model=Assessment)
async def advance_phase(
    assessment_id: int,
    phase: str = Query(..., description="Target phase name"),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """
    Advance assessment to a new phase.
    When phase is 'Afgerond' and type is BIA: triggers BIA calculation + scope writeback.
    """
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    # Validate phase value
    valid_phases = [p.value for p in AssessmentPhase]
    if phase not in valid_phases:
        raise HTTPException(
            status_code=400,
            detail=f"Ongeldige fase. Kies uit: {', '.join(valid_phases)}"
        )

    update_data = {"phase": phase}

    # Auto-manage status based on phase
    if phase == AssessmentPhase.COMPLETED.value:
        update_data["status"] = Status.CLOSED
        update_data["completed_date"] = datetime.utcnow()

        # Auto-trigger BIA calculation for BIA assessments
        if db_assessment.type == AssessmentType.BIA:
            await _calculate_and_writeback_bia(session, db_assessment)

    elif phase == AssessmentPhase.IN_PROGRESS.value:
        if db_assessment.status == Status.DRAFT:
            update_data["status"] = Status.ACTIVE

    elif phase == AssessmentPhase.CANCELLED.value:
        update_data["status"] = Status.CLOSED

    return await crud_assessment.update(session, db_obj=db_assessment, obj_in=update_data)


@router.post("/{assessment_id}/start", response_model=Assessment)
async def start_assessment(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Start an assessment (set status to Active)."""
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    if db_assessment.status != Status.DRAFT:
        raise HTTPException(status_code=400, detail="Assessment must be in Draft status to start")

    return await crud_assessment.update(session, db_obj=db_assessment, obj_in={
        "status": Status.ACTIVE,
        "start_date": datetime.utcnow(),
    })


@router.post("/{assessment_id}/complete", response_model=Assessment)
async def complete_assessment(
    assessment_id: int,
    overall_result: AuditResult,
    executive_summary: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Complete an assessment with results."""
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    if db_assessment.status != Status.ACTIVE:
        raise HTTPException(status_code=400, detail="Assessment must be Active to complete")

    return await crud_assessment.update(session, db_obj=db_assessment, obj_in={
        "status": Status.CLOSED,
        "completed_date": datetime.utcnow(),
        "overall_result": overall_result,
        "executive_summary": executive_summary,
    })


@router.get("/{assessment_id}/summary", response_model=dict)
async def get_assessment_summary(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get summary statistics for an assessment."""
    assessment = await crud_assessment.get_or_404(session, assessment_id)

    # Get findings
    findings = await crud_finding.get_multi_by_field(session, "assessment_id", assessment_id, limit=500)

    # Count by severity
    severity_counts = {s.value: 0 for s in FindingSeverity}
    for finding in findings:
        severity_counts[finding.severity.value] += 1

    # Count by status
    status_counts = {s.value: 0 for s in Status}
    for finding in findings:
        status_counts[finding.status.value] += 1

    return {
        "assessment_id": assessment_id,
        "title": assessment.title,
        "type": assessment.type,
        "status": assessment.status,
        "phase": assessment.phase,
        "overall_result": assessment.overall_result,
        "total_findings": len(findings),
        "findings_by_severity": severity_counts,
        "findings_by_status": status_counts,
        "start_date": assessment.start_date,
        "completed_date": assessment.completed_date,
    }


# =============================================================================
# QUESTIONS & RESPONSES
# =============================================================================

@router.get("/{assessment_id}/questions", response_model=List[AssessmentQuestion])
async def list_assessment_questions(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get questions relevant for an assessment.
    For BIA assessments: returns questions with category starting with 'BIA'.
    """
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    if db_assessment.type == AssessmentType.BIA:
        stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.category.like("BIA%"))
            .where(AssessmentQuestion.is_active == True)  # noqa: E712
            .order_by(AssessmentQuestion.order)
        )
    elif db_assessment.standard_id:
        stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.standard_id == db_assessment.standard_id)
            .where(AssessmentQuestion.is_active == True)  # noqa: E712
            .order_by(AssessmentQuestion.order)
        )
    else:
        stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.is_active == True)  # noqa: E712
            .order_by(AssessmentQuestion.order)
            .limit(100)
        )

    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{assessment_id}/responses", response_model=List[AssessmentResponse])
async def list_assessment_responses(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get all responses for an assessment."""
    await crud_assessment.get_or_404(session, assessment_id)
    return await crud_response.get_multi_by_field(session, "assessment_id", assessment_id, limit=500)


@router.post("/{assessment_id}/responses", response_model=AssessmentResponse)
async def save_assessment_response(
    assessment_id: int,
    response_data: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """
    Upsert a response for a question within an assessment.
    If a response already exists for this assessment+question combo, update it.
    """
    await crud_assessment.get_or_404(session, assessment_id)
    question_id = response_data.get("question_id")
    if not question_id:
        raise HTTPException(status_code=400, detail="question_id is required")

    # Check for existing response
    stmt = (
        select(AssessmentResponse)
        .where(AssessmentResponse.assessment_id == assessment_id)
        .where(AssessmentResponse.question_id == question_id)
    )
    result = await session.execute(stmt)
    existing = result.scalars().first()

    if existing:
        # Update existing
        for key, value in response_data.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        return existing
    else:
        # Create new
        new_response = AssessmentResponse(
            tenant_id=response_data.get("tenant_id", 1),
            assessment_id=assessment_id,
            question_id=question_id,
            response_value=response_data.get("response_value"),
            response_text=response_data.get("response_text"),
            score=response_data.get("score"),
            assessed_by_id=response_data.get("assessed_by_id"),
            assessed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return await crud_response.create(session, obj_in=new_response)


@router.get("/{assessment_id}/progress", response_model=dict)
async def get_assessment_progress(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get progress: how many questions answered vs total."""
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    # Get question count
    if db_assessment.type == AssessmentType.BIA:
        q_stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.category.like("BIA%"))
            .where(AssessmentQuestion.is_active == True)  # noqa: E712
        )
    elif db_assessment.standard_id:
        q_stmt = (
            select(AssessmentQuestion)
            .where(AssessmentQuestion.standard_id == db_assessment.standard_id)
            .where(AssessmentQuestion.is_active == True)  # noqa: E712
        )
    else:
        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.is_active == True)  # noqa: E712

    q_result = await session.execute(q_stmt)
    total = len(q_result.scalars().all())

    # Get response count
    r_result = await session.execute(
        select(AssessmentResponse).where(AssessmentResponse.assessment_id == assessment_id)
    )
    answered = len(r_result.scalars().all())

    pct = round((answered / total) * 100) if total > 0 else 0

    return {"total": total, "answered": answered, "pct": pct}


# =============================================================================
# BIA CALCULATION
# =============================================================================

async def _get_thresholds(session: AsyncSession, tenant_id: Optional[int] = None) -> dict:
    """Get BIA thresholds as score->threshold dict."""
    if tenant_id:
        stmt = select(BIAThreshold).where(BIAThreshold.tenant_id == tenant_id).order_by(BIAThreshold.score)
        result = await session.execute(stmt)
        thresholds = result.scalars().all()
        if thresholds:
            return {t.score: t for t in thresholds}

    stmt = select(BIAThreshold).where(BIAThreshold.tenant_id == None).order_by(BIAThreshold.score)  # noqa: E711
    result = await session.execute(stmt)
    thresholds = result.scalars().all()
    return {t.score: t for t in thresholds}


async def _calculate_and_writeback_bia(session: AsyncSession, assessment: Assessment):
    """Calculate BIA scores from responses and write back to assessment + scope."""
    # Get responses
    responses = await crud_response.get_multi_by_field(
        session, "assessment_id", assessment.id, limit=100
    )
    if not responses:
        return

    # Get questions to map question_id -> order (Q1=1, Q2=2, etc.)
    questions_result = await session.execute(
        select(AssessmentQuestion)
        .where(AssessmentQuestion.category.like("BIA%"))
        .where(AssessmentQuestion.is_active == True)  # noqa: E712
        .order_by(AssessmentQuestion.order)
    )
    questions = questions_result.scalars().all()
    q_order_map = {q.id: q.order for q in questions}

    # Build score map: order -> score (1-4)
    scores = {}
    for resp in responses:
        order = q_order_map.get(resp.question_id)
        if order is not None and resp.score is not None:
            scores[order] = int(resp.score)

    if not scores:
        return

    # Calculate CIA scores
    c_score = max(scores.get(1, 1), scores.get(2, 1))
    i_score = max(scores.get(3, 1), scores.get(4, 1))
    a_score = max(scores.get(5, 1), scores.get(6, 1), scores.get(7, 1), scores.get(8, 1))

    # BCM
    rpo_score = max(scores.get(9, 1), scores.get(10, 1))
    rto_modifier = max(scores.get(11, 1), scores.get(12, 1))
    effective_rto = max(a_score, rto_modifier)

    # Get thresholds
    thresholds = await _get_thresholds(session, assessment.tenant_id if assessment.tenant_id else None)
    if not thresholds:
        return

    # Clamp scores to available thresholds
    max_score = max(thresholds.keys()) if thresholds else 4
    c_score = min(c_score, max_score)
    i_score = min(i_score, max_score)
    a_score = min(a_score, max_score)
    rpo_score = min(rpo_score, max_score)
    effective_rto = min(effective_rto, max_score)

    # Snapshot on assessment
    assessment.bia_cia_label = f"C{c_score}-I{i_score}-A{a_score}"
    assessment.bia_rto_hours = thresholds.get(effective_rto, thresholds.get(1)).rto_hours
    assessment.bia_rpo_hours = thresholds.get(rpo_score, thresholds.get(1)).rpo_hours
    assessment.bia_mtpd_hours = thresholds.get(effective_rto, thresholds.get(1)).mtpd_hours
    assessment.bia_bcp_required = (a_score >= 3) or (effective_rto >= 3)
    session.add(assessment)

    # Scope writeback
    if assessment.scope_id:
        scope_result = await session.execute(
            select(Scope).where(Scope.id == assessment.scope_id)
        )
        scope = scope_result.scalars().first()
        if scope:
            # Map score to ClassificationLevel
            level_map = {
                1: ClassificationLevel.PUBLIC,
                2: ClassificationLevel.INTERNAL,
                3: ClassificationLevel.CONFIDENTIAL,
                4: ClassificationLevel.SECRET,
            }
            scope.confidentiality_rating = level_map.get(c_score, ClassificationLevel.INTERNAL)
            scope.integrity_rating = level_map.get(i_score, ClassificationLevel.INTERNAL)
            scope.availability_rating = level_map.get(a_score, ClassificationLevel.INTERNAL)
            scope.rto_hours = thresholds.get(effective_rto, thresholds.get(1)).rto_hours
            scope.rpo_hours = thresholds.get(rpo_score, thresholds.get(1)).rpo_hours
            scope.mtpd_hours = thresholds.get(effective_rto, thresholds.get(1)).mtpd_hours
            session.add(scope)

    await session.commit()


@router.post("/{assessment_id}/calculate-bia", response_model=dict)
async def calculate_bia(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """
    Calculate BIA scores from responses.
    1. Fetch responses → 2. Calculate C/I/A scores → 3. RTO with modifier
    4. Threshold lookup → 5. Snapshot on Assessment → 6. Writeback to Scope
    """
    db_assessment = await crud_assessment.get_or_404(session, assessment_id)

    if db_assessment.type != AssessmentType.BIA:
        raise HTTPException(status_code=400, detail="BIA berekening is alleen mogelijk voor BIA assessments")

    await _calculate_and_writeback_bia(session, db_assessment)

    # Refresh to get updated values
    await session.refresh(db_assessment)

    return {
        "assessment_id": assessment_id,
        "bia_cia_label": db_assessment.bia_cia_label,
        "bia_rto_hours": db_assessment.bia_rto_hours,
        "bia_rpo_hours": db_assessment.bia_rpo_hours,
        "bia_mtpd_hours": db_assessment.bia_mtpd_hours,
        "bia_bcp_required": db_assessment.bia_bcp_required,
        "scope_id": db_assessment.scope_id,
    }


# =============================================================================
# FINDINGS
# =============================================================================

@router.get("/{assessment_id}/findings", response_model=List[Finding])
async def list_assessment_findings(
    assessment_id: int,
    severity: Optional[FindingSeverity] = Query(None),
    status: Optional[Status] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List findings for an assessment."""
    await crud_assessment.get_or_404(session, assessment_id)

    query = select(Finding).where(Finding.assessment_id == assessment_id)
    if severity:
        query = query.where(Finding.severity == severity)
    if status:
        query = query.where(Finding.status == status)

    result = await session.execute(query)
    return result.scalars().all()


@router.post("/{assessment_id}/findings", response_model=Finding)
async def create_finding(
    assessment_id: int,
    finding: Finding,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Create a finding for an assessment."""
    await crud_assessment.get_or_404(session, assessment_id)

    finding.assessment_id = assessment_id
    return await crud_finding.create(session, obj_in=finding)


@router.get("/findings/{finding_id}", response_model=Finding)
async def get_finding(
    finding_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a finding by ID."""
    return await crud_finding.get_or_404(session, finding_id)


@router.patch("/findings/{finding_id}", response_model=Finding)
async def update_finding(
    finding_id: int,
    finding_update: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Update a finding."""
    db_finding = await crud_finding.get_or_404(session, finding_id)
    return await crud_finding.update(session, db_obj=db_finding, obj_in=finding_update)


@router.post("/findings/{finding_id}/close", response_model=Finding)
async def close_finding(
    finding_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """
    Close a finding.
    Hiaat 7 (ACT-feedbackloop): A finding cannot be closed without
    at least one completed corrective action.
    """
    db_finding = await crud_finding.get_or_404(session, finding_id)

    # ACT-feedbackloop: check for completed corrective actions
    actions = await crud_corrective_action.get_multi_by_field(
        session, "finding_id", finding_id
    )
    if not actions:
        raise HTTPException(
            status_code=400,
            detail="Bevinding kan niet worden afgesloten zonder corrigerende maatregel. "
                   "Maak eerst een actie aan."
        )

    completed_actions = [a for a in actions if a.completed]
    if not completed_actions:
        raise HTTPException(
            status_code=400,
            detail="Bevinding kan niet worden afgesloten: er zijn nog geen afgeronde acties. "
                   "Rond eerst minimaal één actie af."
        )

    return await crud_finding.update(session, db_obj=db_finding, obj_in={"status": Status.CLOSED})


# =============================================================================
# EVIDENCE
# =============================================================================

@router.get("/{assessment_id}/evidence", response_model=List[Evidence])
async def list_assessment_evidence(
    assessment_id: int,
    session: AsyncSession = Depends(get_session),
):
    """List evidence for an assessment."""
    await crud_assessment.get_or_404(session, assessment_id)
    return await crud_evidence.get_multi_by_field(session, "assessment_id", assessment_id)


@router.get("/evidence/", response_model=List[Evidence])
async def list_evidence(
    skip: int = 0,
    limit: int = 100,
    measure_id: Optional[int] = Query(None),
    assessment_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List evidence with optional filters."""
    filters = {}
    if measure_id:
        filters["measure_id"] = measure_id
    if assessment_id:
        filters["assessment_id"] = assessment_id

    return await crud_evidence.get_multi(session, skip=skip, limit=limit, filters=filters)


@router.post("/evidence/", response_model=Evidence)
async def create_evidence(
    evidence: Evidence,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Create new evidence."""
    return await crud_evidence.create(session, obj_in=evidence)


@router.get("/evidence/{evidence_id}", response_model=Evidence)
async def get_evidence(
    evidence_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get evidence by ID."""
    return await crud_evidence.get_or_404(session, evidence_id)


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(
    evidence_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Delete evidence."""
    deleted = await crud_evidence.delete(session, id=evidence_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {"message": "Evidence deleted"}


# =============================================================================
# CORRECTIVE ACTIONS
# =============================================================================

@router.get("/findings/{finding_id}/corrective-actions", response_model=List[CorrectiveAction])
async def list_finding_corrective_actions(
    finding_id: int,
    session: AsyncSession = Depends(get_session),
):
    """List corrective actions for a finding."""
    await crud_finding.get_or_404(session, finding_id)
    return await crud_corrective_action.get_multi_by_field(session, "finding_id", finding_id)


@router.post("/findings/{finding_id}/corrective-actions", response_model=CorrectiveAction)
async def create_corrective_action(
    finding_id: int,
    corrective_action: CorrectiveAction,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Create a corrective action for a finding."""
    await crud_finding.get_or_404(session, finding_id)

    corrective_action.finding_id = finding_id
    return await crud_corrective_action.create(session, obj_in=corrective_action)


@router.get("/corrective-actions/{action_id}", response_model=CorrectiveAction)
async def get_corrective_action(
    action_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a corrective action by ID."""
    return await crud_corrective_action.get_or_404(session, action_id)


@router.patch("/corrective-actions/{action_id}", response_model=CorrectiveAction)
async def update_corrective_action(
    action_id: int,
    action_update: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Update a corrective action."""
    db_action = await crud_corrective_action.get_or_404(session, action_id)
    return await crud_corrective_action.update(session, db_obj=db_action, obj_in=action_update)


@router.post("/corrective-actions/{action_id}/complete", response_model=CorrectiveAction)
async def complete_corrective_action(
    action_id: int,
    completed_by_id: int,
    completion_notes: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_oversight),
):
    """Mark a corrective action as completed."""
    db_action = await crud_corrective_action.get_or_404(session, action_id)

    return await crud_corrective_action.update(session, db_obj=db_action, obj_in={
        "status": Status.CLOSED,
        "completed_date": datetime.utcnow(),
        "completed_by_id": completed_by_id,
        "completion_notes": completion_notes,
    })
