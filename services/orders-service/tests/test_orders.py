from types import SimpleNamespace

import pytest

from tests.conftest import auth_headers


class FakeInventoryClient:
    """Stands in for the gRPC inventory-service client so tests don't need a live Go service."""

    def __init__(self, stock: dict[str, SimpleNamespace]):
        self.stock = stock
        self.reserved: list[tuple[str, int]] = []

    async def batch_get_stock(self, skus):
        return [self.stock[s] for s in skus if s in self.stock]

    async def reserve_stock(self, sku, quantity):
        self.reserved.append((sku, quantity))
        return SimpleNamespace(success=True, message="ok", remaining_quantity=99)


def _stock(sku, price=1.0, qty=10, in_stock=True):
    return SimpleNamespace(sku=sku, unit_price_eur=price, quantity_available=qty, in_stock=in_stock)


@pytest.fixture(autouse=True)
def fake_inventory(monkeypatch):
    fake = FakeInventoryClient({
        "pink-lady-apple": _stock("pink-lady-apple", price=0.65, qty=5),
        "out-of-stock-fruit": _stock("out-of-stock-fruit", in_stock=False),
        "scarce-fruit": _stock("scarce-fruit", qty=1),
    })
    import app.main as main_module
    monkeypatch.setattr(main_module, "inventory_client", fake)
    return fake


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "orders-service"


async def test_create_order_requires_auth(client):
    resp = await client.post("/orders", json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 1}]})
    assert resp.status_code == 401


async def test_create_order_success(client):
    resp = await client.post(
        "/orders",
        json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 2}]},
        headers=auth_headers(),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["total_eur"] == pytest.approx(1.30)
    assert body["items"][0]["fruit_sku"] == "pink-lady-apple"


async def test_create_order_rejects_out_of_stock_item(client):
    resp = await client.post(
        "/orders",
        json={"items": [{"fruit_sku": "out-of-stock-fruit", "quantity": 1}]},
        headers=auth_headers(),
    )
    assert resp.status_code == 400


async def test_create_order_rejects_insufficient_quantity(client):
    resp = await client.post(
        "/orders",
        json={"items": [{"fruit_sku": "scarce-fruit", "quantity": 5}]},
        headers=auth_headers(),
    )
    assert resp.status_code == 400


async def test_list_orders_only_returns_the_current_users_orders(client):
    headers_a = auth_headers("user-a")
    headers_b = auth_headers("user-b")

    await client.post("/orders", json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 1}]}, headers=headers_a)

    resp_a = await client.get("/orders", headers=headers_a)
    resp_b = await client.get("/orders", headers=headers_b)

    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 0


async def test_get_order_not_found(client):
    resp = await client.get("/orders/00000000-0000-0000-0000-000000000000", headers=auth_headers())
    assert resp.status_code == 404


async def test_get_order_returns_404_for_another_users_order(client):
    headers_a = auth_headers("user-a")
    headers_b = auth_headers("user-b")

    create_resp = await client.post(
        "/orders", json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 1}]}, headers=headers_a
    )
    order_id = create_resp.json()["id"]

    resp = await client.get(f"/orders/{order_id}", headers=headers_b)
    assert resp.status_code == 404

    own_resp = await client.get(f"/orders/{order_id}", headers=headers_a)
    assert own_resp.status_code == 200


# ---- Sales summary ----------------------------------------------------------

async def test_sales_summary_requires_auth(client):
    resp = await client.get("/sales/summary?skus=pink-lady-apple")
    assert resp.status_code == 401


async def test_sales_summary_requires_skus(client):
    resp = await client.get("/sales/summary?skus=", headers=auth_headers())
    assert resp.status_code == 400


async def test_sales_summary_aggregates_across_all_buyers(client):
    await client.post(
        "/orders",
        json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 2}]},
        headers=auth_headers("buyer-a"),
    )
    await client.post(
        "/orders",
        json={"items": [{"fruit_sku": "pink-lady-apple", "quantity": 3}]},
        headers=auth_headers("buyer-b"),
    )

    # Requested by a third party (the seller), not either buyer.
    resp = await client.get("/sales/summary?skus=pink-lady-apple", headers=auth_headers("seller-x"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == [
        {"fruit_sku": "pink-lady-apple", "quantity_sold": 5, "revenue_eur": pytest.approx(3.25), "orders_count": 2}
    ]
    assert body["total_quantity_sold"] == 5
    assert body["total_revenue_eur"] == pytest.approx(3.25)


async def test_sales_summary_includes_zero_sales_for_unsold_skus(client):
    resp = await client.get(
        "/sales/summary?skus=pink-lady-apple,never-sold-fruit", headers=auth_headers()
    )
    assert resp.status_code == 200
    body = resp.json()
    never_sold = next(i for i in body["items"] if i["fruit_sku"] == "never-sold-fruit")
    assert never_sold == {"fruit_sku": "never-sold-fruit", "quantity_sold": 0, "revenue_eur": 0.0, "orders_count": 0}
