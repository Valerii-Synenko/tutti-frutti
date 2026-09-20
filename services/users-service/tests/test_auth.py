from jose import jwt

from app.config import settings
from tests.conftest import register_and_login


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "users-service"}


async def test_register_creates_a_non_admin_non_seller_user(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "jane@example.com", "password": "S3curePass!", "full_name": "Jane Doe"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "jane@example.com"
    assert body["is_admin"] is False
    assert body["is_seller"] is False


async def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "S3curePass!", "full_name": "Dupe"}
    first = await client.post("/auth/register", json=payload)
    second = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


async def test_login_returns_token_pair_with_role_claims(client):
    await client.post(
        "/auth/register",
        json={"email": "jane@example.com", "password": "S3curePass!", "full_name": "Jane Doe"},
    )
    resp = await client.post("/auth/login", data={"username": "jane@example.com", "password": "S3curePass!"})
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    claims = jwt.decode(tokens["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert claims["is_admin"] is False
    assert claims["is_seller"] is False


async def test_login_rejects_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "jane@example.com", "password": "S3curePass!", "full_name": "Jane Doe"},
    )
    resp = await client.post("/auth/login", data={"username": "jane@example.com", "password": "wrong"})
    assert resp.status_code == 401


async def test_refresh_issues_a_new_access_token(client):
    tokens = await register_and_login(client)
    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_rejects_an_access_token(client):
    tokens = await register_and_login(client)
    resp = await client.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_returns_the_current_user(client):
    tokens = await register_and_login(client)
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "jane@example.com"


async def test_update_me_changes_full_name(client):
    tokens = await register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.patch("/auth/me", json={"full_name": "Jane Q. Doe"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Jane Q. Doe"


async def test_update_me_rejects_email_already_taken(client):
    await register_and_login(client, email="taken@example.com")
    tokens = await register_and_login(client, email="jane@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.patch("/auth/me", json={"email": "taken@example.com"}, headers=headers)
    assert resp.status_code == 409


async def test_update_me_can_change_password(client):
    tokens = await register_and_login(client, email="jane@example.com", password="S3curePass!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.patch("/auth/me", json={"password": "NewPassw0rd!"}, headers=headers)
    assert resp.status_code == 200

    login_resp = await client.post("/auth/login", data={"username": "jane@example.com", "password": "NewPassw0rd!"})
    assert login_resp.status_code == 200


async def test_become_seller_sets_the_seller_claim(client):
    tokens = await register_and_login(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post("/auth/become-seller", headers=headers)
    assert resp.status_code == 200
    new_tokens = resp.json()

    claims = jwt.decode(new_tokens["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert claims["is_seller"] is True

    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert me_resp.json()["is_seller"] is True


async def test_become_seller_requires_auth(client):
    resp = await client.post("/auth/become-seller")
    assert resp.status_code == 401
