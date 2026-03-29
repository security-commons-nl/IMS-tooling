"""Base agent class — shared logic for all IMS step agents."""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.core_models import (
    AgentConversation,
    AgentMessage,
    AIAuditLog,
    IMSStep,
    IMSStepExecution,
    IMSStepOutputFulfillment,
    IMSDocumentVersion,
)
from app.services import llm_client
from app.services.rag.retrieval_service import search_knowledge

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


class BaseAgent:
    agent_name: str = ""
    step_number: str = ""
    prompt_file: str = ""

    def __init__(self):
        self._base_system = _load_prompt("base_system.txt")
        self._step_prompt = _load_prompt(self.prompt_file) if self.prompt_file else ""

    async def get_context(
        self, execution_id: UUID, db: AsyncSession
    ) -> dict:
        """Load step, execution, tenant info, and prerequisite outputs."""
        result = await db.execute(
            select(IMSStepExecution).where(IMSStepExecution.id == execution_id)
        )
        execution = result.scalar_one()

        result = await db.execute(
            select(IMSStep)
            .options(selectinload(IMSStep.outputs))
            .where(IMSStep.id == execution.step_id)
        )
        step = result.scalar_one()

        # Load fulfilled outputs from prerequisite steps (same tenant)
        prerequisite_docs = await self._load_prerequisite_outputs(
            execution.tenant_id, db
        )

        # RAG: retrieve relevant knowledge chunks
        rag_context = []
        try:
            chunks = await search_knowledge(
                query=f"{step.name} {step.waarom_nu}",
                tenant_id=execution.tenant_id,
                db=db,
                top_k=3,
            )
            rag_context = [c.content for c in chunks]
        except Exception:
            pass  # RAG is optional — don't block agent if it fails

        return {
            "step": step,
            "execution": execution,
            "tenant_id": execution.tenant_id,
            "prerequisite_docs": prerequisite_docs,
            "rag_context": rag_context,
        }

    async def _load_prerequisite_outputs(
        self, tenant_id: UUID, db: AsyncSession
    ) -> list[dict]:
        """Load content_json from fulfilled document versions for this tenant."""
        result = await db.execute(
            select(IMSStepOutputFulfillment).where(
                IMSStepOutputFulfillment.tenant_id == tenant_id,
                IMSStepOutputFulfillment.document_id.isnot(None),
            )
        )
        fulfillments = result.scalars().all()

        docs = []
        for f in fulfillments:
            result = await db.execute(
                select(IMSDocumentVersion).where(
                    IMSDocumentVersion.document_id == f.document_id
                ).order_by(IMSDocumentVersion.created_at.desc()).limit(1)
            )
            version = result.scalar_one_or_none()
            if version and version.content_json:
                docs.append({
                    "document_id": str(f.document_id),
                    "content_json": version.content_json,
                })
        return docs

    def build_system_prompt(self, context: dict) -> str:
        """Construct the system prompt from base + step-specific template."""
        parts = [self._base_system]
        if self._step_prompt:
            parts.append(self._step_prompt)

        step = context["step"]
        parts.append(
            f"\n\nJe werkt aan stap {step.number}: {step.name}.\n"
            f"Waarom nu: {step.waarom_nu}\n"
            f"Gremium: {step.required_gremium}"
        )

        # Add RAG context (normative knowledge)
        if context.get("rag_context"):
            parts.append("\n\n--- Relevante normteksten ---")
            for chunk in context["rag_context"]:
                parts.append(f"\n{chunk}")

        # Add prerequisite context
        if context.get("prerequisite_docs"):
            parts.append("\n\n--- Eerder opgeleverde documenten ---")
            for doc in context["prerequisite_docs"]:
                parts.append(f"\nDocument {doc['document_id']}:\n{doc['content_json']}")

        return "\n\n".join(parts)

    def build_messages(
        self,
        conversation: AgentConversation,
        user_message: str,
        system_prompt: str,
    ) -> list[dict]:
        """Build the full message list for the LLM."""
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (skip system messages already in DB)
        for msg in conversation.messages:
            if msg.role == "system":
                continue
            messages.append({"role": msg.role, "content": msg.content})

        # Add new user message
        messages.append({"role": "user", "content": user_message})
        return messages

    async def chat(
        self,
        conversation: AgentConversation,
        user_message: str,
        context: dict,
        db: AsyncSession,
    ) -> AgentMessage:
        """Send a message and get a response. Persists both messages."""
        system_prompt = self.build_system_prompt(context)
        messages = self.build_messages(conversation, user_message, system_prompt)

        # Save user message
        user_msg = AgentMessage(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )
        db.add(user_msg)

        # Call LLM
        response = await llm_client.chat_completion(messages)

        # Create audit log
        audit_log = AIAuditLog(
            tenant_id=context["tenant_id"],
            agent_name=self.agent_name,
            step_execution_id=context["execution"].id,
            model=response["model"],
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
        )
        db.add(audit_log)
        await db.flush()

        # Save assistant message
        assistant_msg = AgentMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response["content"],
            audit_log_id=audit_log.id,
        )
        db.add(assistant_msg)
        await db.flush()
        await db.refresh(assistant_msg)

        return assistant_msg

    def get_greeting(self) -> str:
        """Initial greeting when conversation starts."""
        return (
            "Welkom bij deze stap. Heeft u al een bestaand document "
            "voor deze stap, of wilt u dat ik u door de vragen leid?"
        )
