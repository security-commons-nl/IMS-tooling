import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.models.core_models import AIKnowledgeBase

logger = logging.getLogger(__name__)


def _build_embeddings():
    """Build embeddings model based on available provider."""
    if settings.MISTRAL_API_KEY:
        try:
            from langchain_mistralai import MistralAIEmbeddings
            return MistralAIEmbeddings(
                api_key=settings.MISTRAL_API_KEY,
                model="mistral-embed",
            )
        except Exception as e:
            logger.warning(f"⚠️ MistralAI embeddings not available: {e}")
    logger.warning("⚠️ No embeddings provider configured — knowledge search disabled")
    return None


class KnowledgeService:
    def __init__(self):
        self.embeddings = _build_embeddings()

    async def add_knowledge(
        self,
        session: AsyncSession,
        key: str,
        title: str,
        content: str,
        category: str
    ) -> AIKnowledgeBase:
        """Add a new knowledge entry and generate its embedding."""
        vector = self.embeddings.embed_query(content) if self.embeddings else None

        knowledge = AIKnowledgeBase(
            key=key,
            title=title,
            content=content,
            category=category,
            is_embedded=vector is not None,
            embedded_at=datetime.utcnow() if vector is not None else None,
            embedding=vector
        )

        session.add(knowledge)
        await session.commit()
        await session.refresh(knowledge)
        return knowledge

    async def search_knowledge(
        self,
        session: AsyncSession,
        query: str,
        limit: int = 3
    ) -> List[AIKnowledgeBase]:
        """Semantic search for knowledge using cosine distance."""
        if not self.embeddings:
            return []

        query_vector = self.embeddings.embed_query(query)

        stmt = select(AIKnowledgeBase).order_by(
            AIKnowledgeBase.embedding.cosine_distance(query_vector)
        ).limit(limit)

        result = await session.exec(stmt)
        return result.all()


knowledge_service = KnowledgeService()
