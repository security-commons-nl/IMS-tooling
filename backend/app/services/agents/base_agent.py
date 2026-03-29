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
    IMSDocument,
    IMSDocumentVersion,
    IMSStep,
    IMSStepExecution,
    IMSStepOutput,
    IMSStepOutputFulfillment,
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

    async def generate_document(
        self,
        conversation: AgentConversation,
        context: dict,
        db: AsyncSession,
    ) -> list[dict]:
        """Generate concept documents for all document/register outputs of this step.

        Decision outputs are skipped — those must be created manually by the gremium.
        Returns a list of {document_id, version_id, output_name, content_json} dicts.
        """
        import json as _json

        step = context["step"]
        execution = context["execution"]

        # Filter: only document and register outputs (not decisions)
        doc_outputs = [
            o for o in step.outputs
            if o.output_type in ("document", "register")
        ]

        if not doc_outputs:
            return []

        # Check which outputs are already fulfilled
        result = await db.execute(
            select(IMSStepOutputFulfillment).where(
                IMSStepOutputFulfillment.step_execution_id == execution.id,
            )
        )
        fulfilled_ids = {f.step_output_id for f in result.scalars().all()}

        unfulfilled = [o for o in doc_outputs if o.id not in fulfilled_ids]
        if not unfulfilled:
            return []

        # Build generation prompt
        output_names = ", ".join(o.name for o in unfulfilled)
        system_prompt = self.build_system_prompt(context)

        gen_prompt = (
            f"Genereer nu de volgende concept-documenten op basis van ons gesprek:\n"
            f"{output_names}\n\n"
            f"Geef je antwoord als JSON object met per document een key (de output-naam) "
            f"en als value een object met 'sections' (array van {{title, content}}) "
            f"en 'metadata' ({{confidence_note: 'AI CONCEPT — verifieer handmatig'}}).\n\n"
            f"Voorbeeld format:\n"
            f'{{"Besluitmemo": {{"sections": [{{"title": "Aanleiding", "content": "..."}}], '
            f'"metadata": {{"confidence_note": "AI CONCEPT"}}}}}}\n\n'
            f"Antwoord ALLEEN met de JSON, geen andere tekst."
        )

        # Build messages including conversation history
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation.messages:
            if msg.role == "system":
                continue
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": gen_prompt})

        response = await llm_client.chat_completion(messages, temperature=0.2)

        # Create audit log
        audit_log = AIAuditLog(
            tenant_id=context["tenant_id"],
            agent_name=self.agent_name,
            step_execution_id=execution.id,
            model=response["model"],
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
        )
        db.add(audit_log)

        # Parse LLM response
        content_text = response["content"].strip()
        if content_text.startswith("```"):
            content_text = content_text.split("\n", 1)[1] if "\n" in content_text else content_text
            if content_text.endswith("```"):
                content_text = content_text[:-3]
            content_text = content_text.strip()

        try:
            generated = _json.loads(content_text)
        except _json.JSONDecodeError:
            logger.warning(f"Failed to parse generate response: {content_text[:200]}")
            # Fallback: use raw text as single document
            generated = {
                unfulfilled[0].name: {
                    "sections": [{"title": "Gegenereerd document", "content": content_text}],
                    "metadata": {"confidence_note": "AI CONCEPT — verifieer handmatig"},
                }
            }

        results = []
        for output in unfulfilled:
            content_json = generated.get(output.name)
            if not content_json:
                # Try to find a close match
                for key in generated:
                    if key.lower() in output.name.lower() or output.name.lower() in key.lower():
                        content_json = generated[key]
                        break

            if not content_json:
                content_json = {
                    "sections": [{"title": output.name, "content": "Nog niet gegenereerd."}],
                    "metadata": {"confidence_note": "AI CONCEPT — onvolledig"},
                }

            # Create document
            doc = IMSDocument(
                tenant_id=context["tenant_id"],
                step_execution_id=execution.id,
                document_type="overig",
                title=output.name,
                visibility="privé",
            )
            db.add(doc)
            await db.flush()

            # Create version
            version = IMSDocumentVersion(
                document_id=doc.id,
                version_number="1.0",
                content_json=content_json,
                status="concept",
                generated_by_agent=self.agent_name,
            )
            db.add(version)
            await db.flush()

            # Create fulfillment
            fulfillment = IMSStepOutputFulfillment(
                tenant_id=context["tenant_id"],
                step_output_id=output.id,
                step_execution_id=execution.id,
                document_id=doc.id,
            )
            db.add(fulfillment)

            results.append({
                "document_id": doc.id,
                "version_id": version.id,
                "output_name": output.name,
                "content_json": content_json,
            })

        # Save assistant message about generation
        gen_msg = AgentMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=f"Ik heb {len(results)} concept-document(en) gegenereerd: "
                    + ", ".join(r["output_name"] for r in results)
                    + ". Deze zijn als concept gekoppeld aan de stap-outputs. "
                    + "Besluiten moeten handmatig worden vastgelegd door het bevoegde gremium.",
            audit_log_id=audit_log.id,
        )
        db.add(gen_msg)
        await db.flush()

        return results

    def get_greeting(self) -> str:
        """Initial greeting when conversation starts."""
        return (
            "Welkom bij deze stap. Heeft u al een bestaand document "
            "voor deze stap, of wilt u dat ik u door de vragen leid?"
        )
