from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.inventory_client import inventory_client

_http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _http_client
    _http_client = httpx.AsyncClient(timeout=10.0)
    yield
    await _http_client.aclose()
    await inventory_client.close()


app = FastAPI(
    title="Tutti Frutti — Gateway (BFF)",
    description="Single entry point for the UI. Aggregates users-service, "
    "catalogue-service, orders-service and fruit-assistant-service over REST, "
    "and enriches catalogue responses with live stock/pricing from "
    "inventory-service over gRPC.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_origin_regex=r"http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _forward_headers(request: Request) -> dict:
    headers = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["authorization"] = auth
    return headers


async def _proxy(method: str, url: str, request: Request, **kwargs) -> Response:
    assert _http_client is not None
    resp = await _http_client.request(
        method, url, headers=_forward_headers(request), **kwargs
    )
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "gateway"}


# ---- Auth (proxied to users-service) --------------------------------------

@app.post("/auth/register", tags=["auth"])
async def register(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/register", request, content=body,
                         headers={"content-type": "application/json"})


@app.post("/auth/login", tags=["auth"])
async def login(request: Request):
    form = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/login", request, content=form,
                         headers={"content-type": request.headers.get("content-type", "application/x-www-form-urlencoded")})


@app.post("/auth/refresh", tags=["auth"])
async def refresh(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/refresh", request, content=body,
                         headers={"content-type": "application/json"})


@app.get("/auth/me", tags=["auth"])
async def me(request: Request):
    return await _proxy("GET", f"{settings.users_service_url}/auth/me", request)


# ---- Fruits (catalogue-service + live enrichment from inventory-service) ---

@app.get("/fruits", tags=["fruits"])
async def list_fruits(request: Request):
    assert _http_client is not None
    resp = await _http_client.get(f"{settings.catalogue_service_url}/fruits", params=dict(request.query_params))
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Catalogue service error")

    fruits = resp.json()
    skus = [f["slug"] for f in fruits]
    stock_by_sku = {}
    if skus:
        try:
            stock_items = await inventory_client.batch_get_stock(skus)
            stock_by_sku = {item.sku: item for item in stock_items}
        except Exception:
            stock_by_sku = {}

    for fruit in fruits:
        stock = stock_by_sku.get(fruit["slug"])
        fruit["live_price_eur"] = stock.unit_price_eur if stock else None
        fruit["quantity_available"] = stock.quantity_available if stock else None
        fruit["in_stock"] = stock.in_stock if stock else False

    return fruits


@app.get("/fruits/{fruit_id}", tags=["fruits"])
async def get_fruit(fruit_id: str, request: Request):
    assert _http_client is not None
    resp = await _http_client.get(f"{settings.catalogue_service_url}/fruits/{fruit_id}")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Fruit not found")

    fruit = resp.json()
    try:
        stock_items = await inventory_client.batch_get_stock([fruit["slug"]])
        stock = stock_items[0] if stock_items else None
    except Exception:
        stock = None

    fruit["live_price_eur"] = stock.unit_price_eur if stock else None
    fruit["quantity_available"] = stock.quantity_available if stock else None
    fruit["in_stock"] = stock.in_stock if stock else False
    return fruit


@app.post("/fruits", tags=["fruits"])
async def create_fruit(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.catalogue_service_url}/fruits", request, content=body,
                         headers={"content-type": "application/json"})


# ---- Orders (proxied to orders-service) ------------------------------------

@app.post("/orders", tags=["orders"])
async def create_order(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.orders_service_url}/orders", request, content=body,
                         headers={"content-type": "application/json"})


@app.get("/orders", tags=["orders"])
async def list_orders(request: Request):
    return await _proxy("GET", f"{settings.orders_service_url}/orders", request)


@app.get("/orders/{order_id}", tags=["orders"])
async def get_order(order_id: str, request: Request):
    return await _proxy("GET", f"{settings.orders_service_url}/orders/{order_id}", request)


# ---- AI assistant (proxied to fruit-assistant-service) --------------------

@app.post("/assistant/chat", tags=["assistant"])
async def chat(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.assistant_service_url}/chat", request, content=body,
                         headers={"content-type": "application/json"})
