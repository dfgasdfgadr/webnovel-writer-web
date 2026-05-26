import os
import tempfile
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, event
from sqlalchemy.pool import NullPool

# Per-process temporary DB to avoid lock conflicts on parallel/repeated runs
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db", prefix="novelcraft_test_")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_test_db_path}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.main import app
from app.database import Base, get_db

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

# Enable WAL mode + shared cache for SQLite concurrency
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

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
        from app.db.schema import sync_sqlite_schema
        await conn.run_sync(sync_sqlite_schema)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    # Clean up temp db file
    try:
        os.close(_test_db_fd)
        os.unlink(_test_db_path)
    except OSError:
        pass


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
