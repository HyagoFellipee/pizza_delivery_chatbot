"""
Database connection and initialization using SQLModel.
"""
from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Convert postgres:// to postgresql:// for SQLAlchemy compatibility
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.ENVIRONMENT == "development",
    future=True
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in SQLModel models.
    """
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models.pizza import Pizza

        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("Database tables created successfully")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Yields an async session for use in API endpoints.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
