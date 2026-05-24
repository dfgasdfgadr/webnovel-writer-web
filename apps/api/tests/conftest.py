import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_novelcraft.db"

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_novelcraft.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_db():
    """Create all tables once for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def _clean_db(_setup_db):
    """Truncate all tables AFTER each test for isolation."""
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await conn.execute(text(f"DELETE FROM {table.name}"))
            except Exception:
                pass  # table might not exist yet during transitional states


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient):
    """Register a test user and return Bearer auth headers."""
    resp = await async_client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpassword",
        "display_name": "Test User",
    })
    if resp.status_code != 201:
        raise RuntimeError(f"Failed to register test user: {resp.text}")
    login_resp = await async_client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "testpassword",
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}
