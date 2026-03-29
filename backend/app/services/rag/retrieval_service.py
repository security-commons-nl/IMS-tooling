"""Knowledge retrieval via pgvector similarity search."""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core_models import IMSKnowledgeChunk
from app.services.rag.embedding_service import generate_embedding


async def search_knowledge(
    query: str,
    tenant_id: UUID | None,
    db: AsyncSession,
    layer: str | None = None,
    top_k: int = 5,
) -> list[IMSKnowledgeChunk]:
    """Search knowledge chunks by semantic similarity.

    Combines normatief (shared, tenant_id IS NULL) and organisatie (tenant-scoped) layers.
    """
    query_embedding = await generate_embedding(query)

    # Build filter: normatief (shared) + tenant-specific
    conditions = []
    if tenant_id:
        conditions.append(
            "(k.tenant_id IS NULL OR k.tenant_id = :tenant_id)"
        )
    else:
        conditions.append("k.tenant_id IS NULL")

    if layer:
        conditions.append("k.layer = :layer")

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    # pgvector cosine distance: <=> operator
    sql = text(f"""
        SELECT k.id, k.layer, k.tenant_id, k.source_type, k.source_id,
               k.chunk_index, k.content, k.model_used,
               k.embedding <=> :embedding AS distance
        FROM ims_knowledge_chunks k
        WHERE {where_clause}
        ORDER BY k.embedding <=> :embedding
        LIMIT :top_k
    """)

    params = {"embedding": str(query_embedding), "top_k": top_k}
    if tenant_id:
        params["tenant_id"] = str(tenant_id)
    if layer:
        params["layer"] = layer

    result = await db.execute(sql, params)
    rows = result.fetchall()

    # Load as ORM objects for consistency
    if not rows:
        return []

    chunk_ids = [row[0] for row in rows]
    result = await db.execute(
        select(IMSKnowledgeChunk).where(IMSKnowledgeChunk.id.in_(chunk_ids))
    )
    chunks = {c.id: c for c in result.scalars().all()}

    # Return in distance order
    return [chunks[row[0]] for row in rows if row[0] in chunks]
