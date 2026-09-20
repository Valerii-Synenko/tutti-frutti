import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    """An httpx client wired to the FastAPI app with an isolated in-memory
    sqlite database per test, so tests never touch the real Postgres instance."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    test_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


async def register_and_login(client: AsyncClient, email: str = "jane@example.com", password: str = "S3curePass!", full_name: str = "Jane Doe") -> dict:
    """Registers a user and returns their token pair as a dict."""
    await client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})
    resp = await client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()
