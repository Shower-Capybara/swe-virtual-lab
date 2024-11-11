from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from config import Config


# Create async engine
engine = create_async_engine(
    f"postgresql+asyncpg://{Config.DB_USER}:{Config.DB_PASSWORD}"
    f"@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}",
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async session"""
    async with async_session_maker() as session:
        yield session