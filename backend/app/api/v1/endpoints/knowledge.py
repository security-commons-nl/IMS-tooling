from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import get_session
from app.models.core_models import AIKnowledgeBase

router = APIRouter()

@router.get("/", response_model=List[AIKnowledgeBase])
async def get_knowledge_entries(
    session: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    search: Optional[str] = None,
) -> Any:
    """
    Retrieve knowledge base entries.
    """
    query = select(AIKnowledgeBase)
    
    if category:
        query = query.where(AIKnowledgeBase.category == category)
    
    if subcategory:
        query = query.where(AIKnowledgeBase.subcategory == subcategory)
        
    if search:
        # Simple text search on title or key
        query = query.where(
            (AIKnowledgeBase.title.ilike(f"%{search}%")) | 
            (AIKnowledgeBase.key.ilike(f"%{search}%"))
        )
        
    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    entries = result.scalars().all()
    
    return entries

@router.get("/{entry_id}", response_model=AIKnowledgeBase)
async def get_knowledge_entry(
    entry_id: int,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get a specific knowledge base entry by ID.
    """
    entry = await session.get(AIKnowledgeBase, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry
