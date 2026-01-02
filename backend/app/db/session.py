"""
Database session management for async SQLAlchemy.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from ..core.config import settings


# Create async engine with connection pooling disabled for serverless compatibility
# In production, you might want to enable pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,  # Disable pooling for Docker/serverless
)

# Session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for scripts
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),  # Remove async driver
    echo=settings.DEBUG,
    poolclass=NullPool,
)

# Sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_sync_session() -> Session:
    """Get a synchronous database session for scripts."""
    return SyncSessionLocal()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Automatically handles session lifecycle (commit/rollback/close).
    
    Yields:
        AsyncSession: Database session for the request.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    Should only be used in development or for testing.
    Use Alembic migrations for production.
    """
    from .base import Base
    from . import models  # noqa: F401 - Import models to register them
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    Should be called during application shutdown.
    """
    await engine.dispose()
