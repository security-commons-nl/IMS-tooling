from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any


# ── AgentConversation ────────────────────────────────────────────────────


class ConversationStartRequest(BaseModel):
    step_execution_id: UUID


class MessageCreate(BaseModel):
    content: str
    input_document_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata_json: Optional[Any] = None
    audit_log_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    step_execution_id: UUID
    agent_name: str
    status: str
    messages: List[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Document generation ──────────────────────────────────────────────────


class GeneratedDocumentItem(BaseModel):
    document_id: UUID
    version_id: UUID
    output_name: str
    content_json: Any


class GenerateDocumentsResponse(BaseModel):
    documents: List[GeneratedDocumentItem]
    message: str


# ── Feedback ─────────────────────────────────────────────────────────────


class FeedbackCreate(BaseModel):
    feedback: str  # "positief" or "negatief"
    comment: Optional[str] = None
