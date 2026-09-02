"""Pytest test fixtures and configuration with NullPool for test isolation."""

import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Create test engine using NullPool so each test/request gets its own fresh connection
db_url = settings.resolved_database_url
if ":5432" in db_url:
    db_url = db_url.replace(":5432", ":5433")

test_engine = create_async_engine(
    db_url,
    poolclass=NullPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncSession:
    """Override get_db for testing with NullPool."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Ensure all tables and new columns exist before tests run."""
    from sqlalchemy import text
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Execute safe auto-migrations for newly added columns
        await conn.execute(text("ALTER TABLE merchants ADD COLUMN IF NOT EXISTS api_key_hash VARCHAR(64);"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price_paise INTEGER;"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_paise BIGINT;"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_paise BIGINT;"))
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Async database session fixture for test functions."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client():
    """Async test client fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac

