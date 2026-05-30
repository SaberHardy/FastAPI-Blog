# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, DeclarativeBase

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URI = 'sqlite+aiosqlite:///./blog.db'

engine = create_async_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}, pool_pre_ping=True)
AsyncSession = async_sessionmaker(engine,
                                  class_=AsyncSession,
                                  expire_on_commit=False  # for async prevent issues with expired objects after commit
                                  )


class Base(DeclarativeBase):
    pass


# Provide the session to our routes
async def get_db():
    async with AsyncSession() as session:
        yield session
