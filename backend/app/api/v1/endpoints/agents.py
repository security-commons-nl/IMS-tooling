"""Agent API — conversation management, chat, document generation, feedback."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.core.auth import CurrentUser, get_current_user, require_role
from app.core.db import get_db
from app.models.core_models import (
    AgentConversation,
    AgentMessage,
    AIAuditLog,
    IMSStep,
    IMSStepExecution,
)
from app.schemas.agents import (
    ConversationStartRequest,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    FeedbackCreate,
    GenerateDocumentsResponse,
    GeneratedDocumentItem,
)
from app.services.agents.registry import get_agent_by_name

router = APIRouter()


# ── Start or resume conversation ─────────────────────────────────────────


@router.post("/{agent_name}/conversations", response_model=ConversationResponse, status_code=201)
async def start_conversation(
    agent_name: str,
    data: ConversationStartRequest,
    current_user: CurrentUser = Depends(require_role("tims_lid")),
    db: AsyncSession = Depends(get_db),
):
    # Validate agent exists
    agent = get_agent_by_name(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' niet gevonden")

    # Validate execution exists and belongs to tenant
    result = await db.execute(
        select(IMSStepExecution).where(
            IMSStepExecution.id == data.step_execution_id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="StepExecution niet gevonden")

    # Validate step matches agent
    result = await db.execute(
        select(IMSStep).where(IMSStep.id == execution.step_id)
    )
    step = result.scalar_one()
    if step.number != agent.step_number:
        raise HTTPException(
            status_code=422,
            detail=f"Agent '{agent_name}' hoort bij stap {agent.step_number}, niet stap {step.number}",
        )

    # Check if conversation already exists (resume)
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(
            AgentConversation.tenant_id == current_user.tenant_id,
            AgentConversation.step_execution_id == data.step_execution_id,
            AgentConversation.agent_name == agent_name,
        )
    )
    conversation = result.scalar_one_or_none()

    if conversation:
        return conversation

    # Create new conversation with greeting
    conversation = AgentConversation(
        tenant_id=current_user.tenant_id,
        step_execution_id=data.step_execution_id,
        agent_name=agent_name,
        status="active",
    )
    db.add(conversation)
    await db.flush()

    # Add greeting message
    greeting = AgentMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=agent.get_greeting(),
    )
    db.add(greeting)
    await db.flush()

    # Reload with messages
    await db.refresh(conversation)
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(AgentConversation.id == conversation.id)
    )
    conversation = result.scalar_one()

    return conversation


# ── Get conversation ─────────────────────────────────────────────────────


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversatie niet gevonden")
    return conversation


# ── Send message ─────────────────────────────────────────────────────────


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    current_user: CurrentUser = Depends(require_role("tims_lid")),
    db: AsyncSession = Depends(get_db),
):
    # Load conversation
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversatie niet gevonden")

    if conversation.status != "active":
        raise HTTPException(
            status_code=422,
            detail="Conversatie is niet meer actief",
        )

    # Get agent
    agent = get_agent_by_name(conversation.agent_name)
    if not agent:
        raise HTTPException(status_code=500, detail="Agent niet gevonden")

    # Get context and chat
    context = await agent.get_context(conversation.step_execution_id, db)
    assistant_msg = await agent.chat(conversation, data.content, context, db)

    return assistant_msg


# ── Feedback ─────────────────────────────────────────────────────────────


@router.post("/conversations/{conversation_id}/feedback", status_code=204)
async def submit_feedback(
    conversation_id: UUID,
    data: FeedbackCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load conversation
    result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversatie niet gevonden")

    # Find the last assistant message with an audit log
    result = await db.execute(
        select(AgentMessage)
        .where(
            AgentMessage.conversation_id == conversation_id,
            AgentMessage.role == "assistant",
            AgentMessage.audit_log_id.isnot(None),
        )
        .order_by(AgentMessage.created_at.desc())
        .limit(1)
    )
    last_msg = result.scalar_one_or_none()
    if not last_msg or not last_msg.audit_log_id:
        raise HTTPException(status_code=404, detail="Geen AI-bericht gevonden om feedback op te geven")

    # Update audit log
    result = await db.execute(
        select(AIAuditLog).where(AIAuditLog.id == last_msg.audit_log_id)
    )
    audit_log = result.scalar_one_or_none()
    if audit_log:
        audit_log.feedback = data.feedback
        audit_log.feedback_comment = data.comment
        await db.flush()


# ── Generate documents ───────────────────────────────────────────────────


@router.post(
    "/conversations/{conversation_id}/generate",
    response_model=GenerateDocumentsResponse,
)
async def generate_documents(
    conversation_id: UUID,
    current_user: CurrentUser = Depends(require_role("tims_lid")),
    db: AsyncSession = Depends(get_db),
):
    # Load conversation
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.messages))
        .where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversatie niet gevonden")

    if conversation.status != "active":
        raise HTTPException(
            status_code=422,
            detail="Conversatie is niet meer actief",
        )

    # Get agent
    agent = get_agent_by_name(conversation.agent_name)
    if not agent:
        raise HTTPException(status_code=500, detail="Agent niet gevonden")

    # Get context and generate
    context = await agent.get_context(conversation.step_execution_id, db)
    results = await agent.generate_document(conversation, context, db)

    if not results:
        raise HTTPException(
            status_code=422,
            detail="Geen document-outputs om te genereren (alle outputs zijn al ingevuld, of er zijn alleen besluit-outputs)",
        )

    documents = [
        GeneratedDocumentItem(
            document_id=r["document_id"],
            version_id=r["version_id"],
            output_name=r["output_name"],
            content_json=r["content_json"],
        )
        for r in results
    ]

    return GenerateDocumentsResponse(
        documents=documents,
        message=f"{len(documents)} concept-document(en) gegenereerd",
    )
