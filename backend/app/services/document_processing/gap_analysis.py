"""Gap analysis — compare uploaded documents against norm requirements."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core_models import (
    IMSGapAnalysisResult,
    IMSStepInputDocument,
    IMSStep,
    IMSStepExecution,
)
from app.services import llm_client

logger = logging.getLogger(__name__)

GAP_ANALYSIS_PROMPT = """Analyseer het volgende document ten opzichte van de normvereisten voor deze stap.

## Stap: {step_name}
## Norm-context: {waarom_nu}

## Document:
{document_text}

## Opdracht:
Identificeer gaps: wat ontbreekt in dit document ten opzichte van wat deze stap vereist?

Geef je antwoord als JSON array met objecten:
[
  {{
    "field_reference": "sectie of onderwerp dat ontbreekt of onvolledig is",
    "ai_suggestion": "wat er zou moeten staan of verbeterd moet worden",
    "uncertainty": true/false (true als je niet zeker bent)
  }}
]

Geef maximaal 10 gaps. Wees specifiek en verwijs naar ISO-clausules waar relevant.
Antwoord ALLEEN met de JSON array, geen andere tekst."""


async def analyze_document(
    document_text: str,
    step_execution_id: UUID,
    input_document_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
) -> list[IMSGapAnalysisResult]:
    """Analyze a document for gaps against the step's norm requirements."""
    # Load step info
    result = await db.execute(
        select(IMSStepExecution).where(IMSStepExecution.id == step_execution_id)
    )
    execution = result.scalar_one()

    result = await db.execute(
        select(IMSStep).where(IMSStep.id == execution.step_id)
    )
    step = result.scalar_one()

    # Truncate document text to avoid exceeding context
    max_chars = 12000
    truncated = document_text[:max_chars]
    if len(document_text) > max_chars:
        truncated += "\n\n[... document afgekapt voor analyse ...]"

    prompt = GAP_ANALYSIS_PROMPT.format(
        step_name=step.name,
        waarom_nu=step.waarom_nu,
        document_text=truncated,
    )

    response = await llm_client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    # Parse response
    content = response["content"].strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        gaps = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse gap analysis response: {content[:200]}")
        gaps = []

    # Create gap analysis results
    results = []
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        gar = IMSGapAnalysisResult(
            input_document_id=input_document_id,
            tenant_id=tenant_id,
            field_reference=gap.get("field_reference", ""),
            ai_suggestion=gap.get("ai_suggestion", ""),
            uncertainty=gap.get("uncertainty", True),
        )
        db.add(gar)
        results.append(gar)

    # Update input document status
    result = await db.execute(
        select(IMSStepInputDocument).where(IMSStepInputDocument.id == input_document_id)
    )
    input_doc = result.scalar_one()
    input_doc.status = "pending_review"

    await db.flush()
    return results
