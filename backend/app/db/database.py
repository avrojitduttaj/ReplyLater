import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger("replylater.db")

# Detect database dialect
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Engine options
engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, echo=False, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and pgvector extension if Postgres."""
    # Ensure models are registered on Base
    import app.db.models  # noqa: F401
    from sqlalchemy import text

    async with engine.begin() as conn:
        if not is_sqlite:
            # Enable pgvector on PostgreSQL
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("Enabled PostgreSQL pgvector extension.")
            except Exception as e:
                logger.warning(f"Could not enable pgvector extension automatically: {e}")

        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
