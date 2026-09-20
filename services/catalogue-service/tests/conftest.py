from datetime import datetime, timedelta, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from mongomock_motor import AsyncMongoMockClient

import app.database as db_module
from app.config import settings
from app.main import app


def make_access_token(user_id: str, is_admin: bool = False, is_seller: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "is_admin": is_admin,
        "is_seller": is_seller,
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def auth_headers(user_id: str = "user-1", is_admin: bool = False, is_seller: bool = False) -> dict:
    return {"Authorization": f"Bearer {make_access_token(user_id, is_admin, is_seller)}"}


@pytest_asyncio.fixture(autouse=True)
async def fake_mongo(monkeypatch):
    """Every test gets a fresh in-memory Mongo double, so listings never leak between tests."""
    monkeypatch.setattr(db_module, "_client", AsyncMongoMockClient())


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
