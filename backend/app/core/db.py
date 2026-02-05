from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True, future=True)

# Alias for clarity in imports
async_engine = engine

async def init_db():
    async with engine.begin() as conn:
        from sqlalchemy import text
        # Only enable vector extension for PostgreSQL
        if "postgresql" in settings.SQLALCHEMY_DATABASE_URI:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
