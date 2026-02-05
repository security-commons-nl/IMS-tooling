from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_
from pydantic import BaseModel

from app.core.db import get_session
from app.models.core_models import (
    CorrectiveAction,
    ReviewSchedule,
    WorkflowInstance,
    WorkflowStatus,
)

router = APIRouter()

# Response Models
class TaskItem(BaseModel):
    id: str  # Unique ID for frontend key
    type: str  # "Corrective Action", "Review", "Approval", "Workflow Task"
    title: str
    due_date: Optional[datetime] = None
    priority: Optional[str] = "Medium"
    status: str
    entity_id: int
    entity_type: str
    link: Optional[str] = None  # Frontend link hint

class TaskSummary(BaseModel):
    total: int
    overdue: int
    due_soon: int  # Due within 7 days

class MyTasksResponse(BaseModel):
    summary: TaskSummary
    tasks: List[TaskItem]

@router.get("/my-tasks", response_model=MyTasksResponse)
async def get_my_tasks(
    # SECURITY TODO: Replace these query params with auth dependencies:
    # user_id should come from: Depends(get_current_user) -> current_user.id
    # tenant_id should come from: Depends(get_current_tenant) -> tenant_id
    # NEVER trust client-provided user_id - this creates an IDOR vulnerability
    user_id: int = Query(..., description="ID of the user (TEMPORARY - must come from auth)"),
    tenant_id: int = Query(..., description="Tenant context (REQUIRED to prevent cross-tenant leakage)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a unified list of tasks for the user.
    Includes:
    - Corrective Actions assigned to the user
    - Scheduled Reviews responsible by the user
    - Workflow approvals/tasks assigned to the user
    
    SECURITY NOTE: tenant_id is required to enforce tenant isolation.
    """
    tasks: List[TaskItem] = []
    now = datetime.utcnow()
    due_soon_threshold = now + timedelta(days=7)

    # 1. Corrective Actions
    query_actions = select(CorrectiveAction).where(
        CorrectiveAction.tenant_id == tenant_id,  # SECURITY: tenant filter ALWAYS applied
        CorrectiveAction.assigned_to_id == user_id,
        CorrectiveAction.completed == False
    )

    result_actions = await session.execute(query_actions)
    actions = result_actions.scalars().all()

    for action in actions:
        tasks.append(TaskItem(
            id=f"action_{action.id}",
            type="Corrective Action",
            title=action.title,
            due_date=action.due_date,
            priority=action.priority.value if action.priority else "Medium",
            status="Open",
            entity_id=action.id if action.id else 0,
            entity_type="CorrectiveAction",
            link=f"/actions/{action.id}"
        ))

    # 2. Review Schedules
    query_reviews = select(ReviewSchedule).where(
        ReviewSchedule.tenant_id == tenant_id,  # SECURITY: tenant filter ALWAYS applied
        ReviewSchedule.responsible_id == user_id,
        ReviewSchedule.is_active == True,
        ReviewSchedule.next_review <= now + timedelta(days=30)
    )

    result_reviews = await session.execute(query_reviews)
    reviews = result_reviews.scalars().all()

    for review in reviews:
        tasks.append(TaskItem(
            id=f"review_{review.id}",
            type="Review",
            title=f"Review: {review.title}",
            due_date=review.next_review,
            priority="Medium", # Reviews usually don't have explicit priority in model
            status="Pending",
            entity_id=review.entity_id,
            entity_type=review.entity_type, # e.g. "Policy", "Risk"
            link=f"/reviews/{review.id}" # Frontend likely needs specific handling
        ))

    # 3. Workflow Instances
    # Tasks where user is assignee OR approver
    query_workflows = select(WorkflowInstance).where(
        WorkflowInstance.tenant_id == tenant_id,  # SECURITY: tenant filter ALWAYS applied
        or_(
            WorkflowInstance.current_assignee_id == user_id,
            WorkflowInstance.current_approver_id == user_id
        ),
        WorkflowInstance.status.in_([WorkflowStatus.IN_PROGRESS, WorkflowStatus.WAITING_APPROVAL])
    )

    result_workflows = await session.execute(query_workflows)
    workflows = result_workflows.scalars().all()

    for wf in workflows:
        is_approval = wf.current_approver_id == user_id and wf.status == WorkflowStatus.WAITING_APPROVAL
        task_type = "Approval" if is_approval else "Workflow Task"

        tasks.append(TaskItem(
            id=f"workflow_{wf.id}",
            type=task_type,
            title=f"{task_type} for {wf.entity_type} #{wf.entity_id}",
            due_date=wf.current_state_deadline,
            priority="High" if is_approval else "Medium",
            status=wf.status.value,
            entity_id=wf.entity_id,
            entity_type=wf.entity_type,
            link=f"/workflows/{wf.id}"
        ))

    # Sort by due date (nulls last)
    tasks.sort(key=lambda x: x.due_date or datetime.max)

    # Summary
    total = len(tasks)
    overdue = sum(1 for t in tasks if t.due_date and t.due_date < now)
    due_soon = sum(1 for t in tasks if t.due_date and now <= t.due_date <= due_soon_threshold)

    return MyTasksResponse(
        summary=TaskSummary(
            total=total,
            overdue=overdue,
            due_soon=due_soon
        ),
        tasks=tasks
    )
