from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Determine DB URL
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    async_db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://") if "aiosqlite" not in db_url else db_url
    sync_db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
else:
    async_db_url = db_url
    sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://").replace("postgresql://", "postgresql+psycopg2://")

try:
    async_engine = create_async_engine(
        async_db_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
except Exception:
    try:
        async_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    except Exception:
        async_engine = None

if async_engine is not None:
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    AsyncSessionLocal = None


try:
    import psycopg2
    sync_engine = create_engine(sync_db_url, echo=False, pool_pre_ping=True)
except Exception:
    # Fallback to local SQLite DB when PostgreSQL service or driver is offline
    sync_engine = create_engine("sqlite:///./llm_eval.db", echo=False)

SyncSessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for obtaining an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
