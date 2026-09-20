"""Exercises every REST method the gateway exposes, verifying each one actually
proxies to the right upstream service with the right method/path/body. This is
the gap that prompted adding these tests in the first place: several fruit
endpoints (PATCH/DELETE, moderation) existed in catalogue-service but were
never wired up through the gateway.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import respx
from httpx import Response

from app.config import settings
import app.main as main_module


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "gateway"}


# ---- Auth --------------------------------------------------------------

async def test_register_proxies_to_users_service(client, mock_upstream):
    route = mock_upstream.post(f"{settings.users_service_url}/auth/register").mock(
        return_value=Response(201, json={"id": "u1", "email": "jane@example.com", "full_name": "Jane"})
    )
    resp = await client.post("/auth/register", json={"email": "jane@example.com", "password": "x", "full_name": "Jane"})
    assert route.called
    assert resp.status_code == 201
    assert resp.json()["email"] == "jane@example.com"


async def test_login_proxies_to_users_service(client, mock_upstream):
    route = mock_upstream.post(f"{settings.users_service_url}/auth/login").mock(
        return_value=Response(200, json={"access_token": "a", "refresh_token": "r", "token_type": "bearer"})
    )
    resp = await client.post("/auth/login", data={"username": "jane@example.com", "password": "x"})
    assert route.called
    assert resp.status_code == 200


async def test_refresh_proxies_to_users_service(client, mock_upstream):
    route = mock_upstream.post(f"{settings.users_service_url}/auth/refresh").mock(
        return_value=Response(200, json={"access_token": "a", "token_type": "bearer"})
    )
    resp = await client.post("/auth/refresh", json={"refresh_token": "r"})
    assert route.called
    assert resp.status_code == 200


async def test_me_proxies_to_users_service(client, mock_upstream):
    route = mock_upstream.get(f"{settings.users_service_url}/auth/me").mock(
        return_value=Response(200, json={"id": "u1", "email": "jane@example.com", "full_name": "Jane", "is_admin": False, "is_seller": False})
    )
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


async def test_update_me_proxies_with_patch(client, mock_upstream):
    route = mock_upstream.patch(f"{settings.users_service_url}/auth/me").mock(
        return_value=Response(200, json={"id": "u1", "email": "jane@example.com", "full_name": "Jane Q.", "is_admin": False, "is_seller": False})
    )
    resp = await client.patch("/auth/me", json={"full_name": "Jane Q."}, headers={"Authorization": "Bearer t"})
    assert route.called
    assert route.calls.last.request.method == "PATCH"
    assert resp.status_code == 200


async def test_become_seller_proxies_to_users_service(client, mock_upstream):
    route = mock_upstream.post(f"{settings.users_service_url}/auth/become-seller").mock(
        return_value=Response(200, json={"access_token": "a", "refresh_token": "r", "token_type": "bearer"})
    )
    resp = await client.post("/auth/become-seller", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


# ---- Fruits --------------------------------------------------------------

async def test_list_fruits_enriches_with_stock(client, mock_upstream, monkeypatch):
    mock_upstream.get(f"{settings.catalogue_service_url}/fruits").mock(
        return_value=Response(200, json=[{"_id": "1", "slug": "kent-mango", "name": "Kent Mango"}])
    )
    fake_stock = AsyncMock(return_value=[SimpleNamespace(sku="kent-mango", unit_price_eur=1.5, quantity_available=10, in_stock=True)])
    monkeypatch.setattr(main_module.inventory_client, "batch_get_stock", fake_stock)

    resp = await client.get("/fruits")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["live_price_eur"] == 1.5
    assert body["in_stock"] is True


async def test_get_fruit_proxies_to_catalogue_service(client, mock_upstream, monkeypatch):
    mock_upstream.get(f"{settings.catalogue_service_url}/fruits/kent-mango").mock(
        return_value=Response(200, json={"_id": "1", "slug": "kent-mango", "name": "Kent Mango"})
    )
    monkeypatch.setattr(main_module.inventory_client, "batch_get_stock", AsyncMock(return_value=[]))

    resp = await client.get("/fruits/kent-mango")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "kent-mango"


async def test_create_fruit_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.catalogue_service_url}/fruits").mock(
        return_value=Response(201, json={"_id": "1", "slug": "kent-mango", "name": "Kent Mango"})
    )
    resp = await client.post("/fruits", json={"name": "Kent Mango", "slug": "kent-mango"}, headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 201


async def test_update_fruit_proxies_with_patch(client, mock_upstream):
    route = mock_upstream.patch(f"{settings.catalogue_service_url}/fruits/1").mock(
        return_value=Response(200, json={"_id": "1", "slug": "kent-mango", "name": "Updated"})
    )
    resp = await client.patch("/fruits/1", json={"name": "Updated"}, headers={"Authorization": "Bearer t"})
    assert route.called
    assert route.calls.last.request.method == "PATCH"
    assert resp.status_code == 200


async def test_delete_fruit_proxies_with_delete(client, mock_upstream):
    route = mock_upstream.delete(f"{settings.catalogue_service_url}/fruits/1").mock(return_value=Response(204))
    resp = await client.delete("/fruits/1", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 204


async def test_list_my_fruits_proxies_to_fruits_mine(client, mock_upstream):
    route = mock_upstream.get(f"{settings.catalogue_service_url}/fruits/mine").mock(return_value=Response(200, json=[]))
    resp = await client.get("/fruits/mine", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


async def test_list_pending_fruits_proxies_to_fruits_pending(client, mock_upstream):
    route = mock_upstream.get(f"{settings.catalogue_service_url}/fruits/pending").mock(return_value=Response(200, json=[]))
    resp = await client.get("/fruits/pending", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


async def test_approve_fruit_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.catalogue_service_url}/fruits/1/approve").mock(
        return_value=Response(200, json={"_id": "1", "status": "approved"})
    )
    resp = await client.post("/fruits/1/approve", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


async def test_reject_fruit_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.catalogue_service_url}/fruits/1/reject").mock(
        return_value=Response(200, json={"_id": "1", "status": "rejected"})
    )
    resp = await client.post("/fruits/1/reject", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


# ---- Orders --------------------------------------------------------------

async def test_create_order_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.orders_service_url}/orders").mock(
        return_value=Response(201, json={"id": "o1", "status": "confirmed", "total_eur": 1.0, "created_at": "2026-01-01T00:00:00Z", "items": []})
    )
    resp = await client.post("/orders", json={"items": [{"fruit_sku": "kent-mango", "quantity": 1}]}, headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 201


async def test_list_orders_proxies_to_orders_service(client, mock_upstream):
    route = mock_upstream.get(f"{settings.orders_service_url}/orders").mock(return_value=Response(200, json=[]))
    resp = await client.get("/orders", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


async def test_get_order_proxies_to_orders_service(client, mock_upstream):
    route = mock_upstream.get(f"{settings.orders_service_url}/orders/o1").mock(
        return_value=Response(200, json={"id": "o1", "status": "confirmed", "total_eur": 1.0, "created_at": "2026-01-01T00:00:00Z", "items": []})
    )
    resp = await client.get("/orders/o1", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 200


# ---- Comments --------------------------------------------------------------

async def test_list_comments_proxies_to_catalogue_service(client, mock_upstream):
    route = mock_upstream.get(f"{settings.catalogue_service_url}/fruits/kent-mango/comments").mock(return_value=Response(200, json=[]))
    resp = await client.get("/fruits/kent-mango/comments")
    assert route.called
    assert resp.status_code == 200


async def test_add_comment_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.catalogue_service_url}/fruits/kent-mango/comments").mock(
        return_value=Response(201, json={"_id": "c1", "fruit_slug": "kent-mango", "author": "Jane", "body": "Nice", "created_at": "2026-01-01T00:00:00Z"})
    )
    resp = await client.post("/fruits/kent-mango/comments", json={"author": "Jane", "body": "Nice"}, headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 201


async def test_delete_comment_proxies_with_delete(client, mock_upstream):
    route = mock_upstream.delete(f"{settings.catalogue_service_url}/fruits/kent-mango/comments/c1").mock(return_value=Response(204))
    resp = await client.delete("/fruits/kent-mango/comments/c1", headers={"Authorization": "Bearer t"})
    assert route.called
    assert resp.status_code == 204


# ---- Assistant --------------------------------------------------------------

async def test_chat_proxies_with_post(client, mock_upstream):
    route = mock_upstream.post(f"{settings.assistant_service_url}/chat").mock(
        return_value=Response(200, json={"reply": "Try a mango!", "used_fallback": False})
    )
    resp = await client.post("/assistant/chat", json={"message": "hi", "history": []})
    assert route.called
    assert resp.status_code == 200
