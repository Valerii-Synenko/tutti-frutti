import httpx
import pytest_asyncio
import respx
from httpx import ASGITransport, AsyncClient

import app.main as main_module
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def http_client():
    """_http_client is normally created in the app's lifespan (never triggered
    under ASGITransport), so tests wire up their own — respx intercepts it."""
    real_client = httpx.AsyncClient(timeout=10.0)
    main_module._http_client = real_client
    yield real_client
    await real_client.aclose()
    main_module._http_client = None


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def mock_upstream():
    with respx.mock(assert_all_called=False) as mock:
        yield mock
