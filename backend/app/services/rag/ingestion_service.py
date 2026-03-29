"""Knowledge ingestion — chunk, embed, and store text."""

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core_models import IMSKnowledgeChunk
from app.services.rag.embedding_service import chunk_text, generate_embedding


async def ingest_text(
    content: str,
    source_type: str,
    source_id: UUID | None,
    tenant_id: UUID | None,
    layer: str,
    model_used: str,
    db: AsyncSession,
) -> list[IMSKnowledgeChunk]:
    """Chunk text, generate embeddings, and store in knowledge chunks.

    Args:
        content: The full text to ingest
        source_type: "standaard", "blueprint", "beleid", "besluit", "handboek_versie"
        source_id: Optional reference to source entity
        tenant_id: None for normatief layer, UUID for organisatie layer
        layer: "normatief" or "organisatie"
        model_used: Name of the embedding model used
        db: Database session
    """
    chunks = chunk_text(content)
    stored = []

    for i, chunk_content in enumerate(chunks):
        embedding = await generate_embedding(chunk_content)

        chunk = IMSKnowledgeChunk(
            id=uuid.uuid4(),
            layer=layer,
            tenant_id=tenant_id,
            source_type=source_type,
            source_id=source_id,
            chunk_index=i,
            content=chunk_content,
            embedding=embedding,
            model_used=model_used,
        )
        db.add(chunk)
        stored.append(chunk)

    await db.flush()
    return stored
