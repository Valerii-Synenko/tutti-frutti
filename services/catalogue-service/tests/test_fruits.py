from tests.conftest import auth_headers

FRUIT_PAYLOAD = {
    "name": "Kent Mango",
    "slug": "kent-mango",
    "description": "Sweet, fiberless mango.",
    "origin": "Peru",
    "is_organic": True,
    "seasonal_months": [11, 12, 1],
    "tags": ["tropical"],
    "image_url": None,
    "base_price_hint_eur": 1.2,
    "attributes": {},
}


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "catalogue-service"


async def test_create_fruit_requires_seller_status(client):
    resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers(is_seller=False, is_admin=False))
    assert resp.status_code == 403


async def test_create_fruit_requires_auth(client):
    resp = await client.post("/fruits", json=FRUIT_PAYLOAD)
    assert resp.status_code == 401


async def test_seller_created_fruit_is_pending_and_hidden_from_public_listing(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["status"] == "pending"
    assert body["seller_id"] == "seller-1"

    listing = await client.get("/fruits")
    assert listing.status_code == 200
    assert all(f["slug"] != "kent-mango" for f in listing.json())


async def test_admin_created_fruit_is_approved_immediately(client):
    resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("admin-1", is_admin=True))
    assert resp.status_code == 201
    assert resp.json()["status"] == "approved"

    listing = await client.get("/fruits")
    assert any(f["slug"] == "kent-mango" for f in listing.json())


async def test_create_fruit_rejects_duplicate_slug(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    assert resp.status_code == 409


async def test_get_fruit_by_slug(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("admin-1", is_admin=True))
    resp = await client.get("/fruits/kent-mango")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Kent Mango"


async def test_get_fruit_not_found(client):
    resp = await client.get("/fruits/does-not-exist")
    assert resp.status_code == 404


async def test_list_mine_only_shows_the_sellers_own_fruit_regardless_of_status(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    other_payload = {**FRUIT_PAYLOAD, "slug": "other-fruit", "name": "Other Fruit"}
    await client.post("/fruits", json=other_payload, headers=auth_headers("seller-2", is_seller=True))

    resp = await client.get("/fruits/mine", headers=auth_headers("seller-1", is_seller=True))
    assert resp.status_code == 200
    slugs = [f["slug"] for f in resp.json()]
    assert slugs == ["kent-mango"]


async def test_list_mine_requires_seller_status(client):
    resp = await client.get("/fruits/mine", headers=auth_headers("plain-user"))
    assert resp.status_code == 403


async def test_list_pending_is_admin_only(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))

    forbidden = await client.get("/fruits/pending", headers=auth_headers("seller-1", is_seller=True))
    assert forbidden.status_code == 403

    resp = await client.get("/fruits/pending", headers=auth_headers("admin-1", is_admin=True))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_approve_fruit_puts_it_on_the_shelf(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    forbidden = await client.post(f"/fruits/{fruit_id}/approve", headers=auth_headers("seller-1", is_seller=True))
    assert forbidden.status_code == 403

    resp = await client.post(f"/fruits/{fruit_id}/approve", headers=auth_headers("admin-1", is_admin=True))
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    listing = await client.get("/fruits")
    assert any(f["slug"] == "kent-mango" for f in listing.json())


async def test_reject_fruit_keeps_it_off_the_shelf(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    resp = await client.post(f"/fruits/{fruit_id}/reject", headers=auth_headers("admin-1", is_admin=True))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


async def test_update_fruit_requires_ownership(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    forbidden = await client.patch(
        f"/fruits/{fruit_id}", json={"description": "hijacked"}, headers=auth_headers("seller-2", is_seller=True)
    )
    assert forbidden.status_code == 403

    resp = await client.patch(
        f"/fruits/{fruit_id}", json={"description": "updated"}, headers=auth_headers("seller-1", is_seller=True)
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "updated"


async def test_admin_can_update_any_fruit(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    resp = await client.patch(
        f"/fruits/{fruit_id}", json={"description": "admin edit"}, headers=auth_headers("admin-1", is_admin=True)
    )
    assert resp.status_code == 200


async def test_delete_fruit_requires_ownership(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    forbidden = await client.delete(f"/fruits/{fruit_id}", headers=auth_headers("seller-2", is_seller=True))
    assert forbidden.status_code == 403

    resp = await client.delete(f"/fruits/{fruit_id}", headers=auth_headers("seller-1", is_seller=True))
    assert resp.status_code == 204


async def test_admin_can_delete_any_fruit(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    resp = await client.delete(f"/fruits/{fruit_id}", headers=auth_headers("admin-1", is_admin=True))
    assert resp.status_code == 204

    get_resp = await client.get(f"/fruits/{FRUIT_PAYLOAD['slug']}")
    assert get_resp.status_code == 404


async def test_delete_fruit_requires_auth(client):
    create_resp = await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("seller-1", is_seller=True))
    fruit_id = create_resp.json()["_id"]

    resp = await client.delete(f"/fruits/{fruit_id}")
    assert resp.status_code == 401


# ---- Comments ---------------------------------------------------------------

async def test_comments_lifecycle(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("admin-1", is_admin=True))
    slug = FRUIT_PAYLOAD["slug"]

    empty = await client.get(f"/fruits/{slug}/comments")
    assert empty.status_code == 200 and empty.json() == []

    create_resp = await client.post(
        f"/fruits/{slug}/comments",
        json={"author": "Maria", "body": "Delicious!"},
        headers=auth_headers("user-1"),
    )
    assert create_resp.status_code == 201
    comment_id = create_resp.json()["_id"]

    listing = await client.get(f"/fruits/{slug}/comments")
    assert len(listing.json()) == 1

    delete_resp = await client.delete(f"/fruits/{slug}/comments/{comment_id}", headers=auth_headers("user-1"))
    assert delete_resp.status_code == 204


async def test_add_comment_requires_auth(client):
    await client.post("/fruits", json=FRUIT_PAYLOAD, headers=auth_headers("admin-1", is_admin=True))
    resp = await client.post(
        f"/fruits/{FRUIT_PAYLOAD['slug']}/comments", json={"author": "Maria", "body": "Nice"}
    )
    assert resp.status_code == 401


async def test_add_comment_to_missing_fruit_returns_404(client):
    resp = await client.post(
        "/fruits/does-not-exist/comments", json={"author": "Maria", "body": "Nice"}, headers=auth_headers()
    )
    assert resp.status_code == 404
