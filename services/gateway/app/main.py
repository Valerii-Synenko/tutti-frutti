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


@app.middleware("http")
async def no_store(request: Request, call_next):
    """Every response here is user- and role-specific (auth, orders, seller
    listings, moderation queue). Without this, browsers can serve a previous
    user's response for the same URL from the session history cache on
    back/forward navigation instead of hitting the network."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


def _forward_headers(request: Request) -> dict:
    headers = {}
    auth = request.headers.get("authorization")
    if auth:
        headers["authorization"] = auth
    return headers


async def _proxy(method: str, url: str, request: Request, **kwargs) -> Response:
    assert _http_client is not None
    headers = {**_forward_headers(request), **kwargs.pop("headers", {})}
    resp = await _http_client.request(method, url, headers=headers, **kwargs)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


def _example(value: object) -> dict:
    """Wraps a raw example value as a named OpenAPI `examples` entry.

    Zudoku's "Use Example" dropdown reads `content.examples` (a named map) and
    renders each entry's `summary`/`name`. The singular `example` field gets
    normalized to a single entry with an empty name, which shows as a blank
    row in the dropdown — so we always use the named form instead.
    """
    return {"default": {"summary": "Example", "value": value}}


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "gateway"}


# ---- Auth (proxied to users-service) --------------------------------------

@app.post(
    "/auth/register",
    tags=["auth"],
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({
                        "email": "jane@example.com",
                        "password": "S3curePass!",
                        "full_name": "Jane Doe",
                    })
                }
            },
        },
        "responses": {
            "201": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "email": "jane@example.com",
                            "full_name": "Jane Doe",
                        })
                    }
                },
            }
        },
    },
)
async def register(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/register", request, content=body,
                         headers={"content-type": "application/json"})


@app.post(
    "/auth/login",
    tags=["auth"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "examples": _example({
                        "username": "jane@example.com",
                        "password": "S3curePass!",
                    })
                }
            },
        },
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                        })
                    }
                },
            }
        },
    },
)
async def login(request: Request):
    form = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/login", request, content=form,
                         headers={"content-type": request.headers.get("content-type", "application/x-www-form-urlencoded")})


@app.post(
    "/auth/refresh",
    tags=["auth"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."})
                }
            },
        },
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                        })
                    }
                },
            }
        },
    },
)
async def refresh(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.users_service_url}/auth/refresh", request, content=body,
                         headers={"content-type": "application/json"})


@app.get(
    "/auth/me",
    tags=["auth"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "email": "jane@example.com",
                            "full_name": "Jane Doe",
                        })
                    }
                },
            }
        },
    },
)
async def me(request: Request):
    return await _proxy("GET", f"{settings.users_service_url}/auth/me", request)


@app.patch(
    "/auth/me",
    tags=["auth"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({"full_name": "Jane Q. Doe"})
                }
            },
        },
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "email": "jane@example.com",
                            "full_name": "Jane Q. Doe",
                            "is_admin": False,
                            "is_seller": False,
                        })
                    }
                },
            }
        },
    },
)
async def update_me(request: Request):
    body = await request.body()
    return await _proxy("PATCH", f"{settings.users_service_url}/auth/me", request, content=body,
                         headers={"content-type": "application/json"})


@app.post(
    "/auth/become-seller",
    tags=["auth"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "token_type": "bearer",
                        })
                    }
                },
            }
        },
    },
)
async def become_seller(request: Request):
    return await _proxy("POST", f"{settings.users_service_url}/auth/become-seller", request)


# ---- Fruits (catalogue-service + live enrichment from inventory-service) ---

_FRUIT_EXAMPLE = {
    "name": "Pink Lady Apple",
    "slug": "pink-lady-apple",
    "description": "Crisp, sweet-tart apple with a rosy blush.",
    "origin": "Italy",
    "is_organic": True,
    "seasonal_months": [9, 10, 11, 12, 1],
    "tags": ["crisp", "snack", "lunchbox"],
    "image_url": "/images/pink-lady-apple.svg",
    "base_price_hint_eur": 0.6,
    "attributes": {
        "shelf_life_days": 45,
        "storage": "refrigerated",
        "allergen_notes": None,
    },
    "_id": "6a48056f850cca8e87c51014",
    "live_price_eur": 0.65,
    "quantity_available": 240,
    "in_stock": True,
}


@app.get(
    "/fruits",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example([_FRUIT_EXAMPLE])}},
            }
        },
    },
)
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


@app.get(
    "/fruits/mine",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example([_FRUIT_EXAMPLE])}},
            }
        },
    },
)
async def list_my_fruits(request: Request):
    return await _proxy("GET", f"{settings.catalogue_service_url}/fruits/mine", request)


@app.get(
    "/fruits/pending",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example([_FRUIT_EXAMPLE])}},
            }
        },
    },
)
async def list_pending_fruits(request: Request):
    return await _proxy("GET", f"{settings.catalogue_service_url}/fruits/pending", request)


@app.get(
    "/fruits/{fruit_id}",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_FRUIT_EXAMPLE)}},
            }
        },
    },
)
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


@app.post(
    "/fruits",
    tags=["fruits"],
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({
                        "name": "Kent Mango",
                        "slug": "kent-mango",
                        "description": "Sweet, fiberless mango with deep orange flesh.",
                        "origin": "Peru",
                        "is_organic": True,
                        "seasonal_months": [11, 12, 1, 2],
                        "tags": ["tropical", "sweet"],
                        "image_url": "/images/kent-mango.svg",
                        "base_price_hint_eur": 1.2,
                        "attributes": {"shelf_life_days": 10, "storage": "room-temperature"},
                    })
                }
            },
        },
        "responses": {
            "201": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "name": "Kent Mango",
                            "slug": "kent-mango",
                            "description": "Sweet, fiberless mango with deep orange flesh.",
                            "origin": "Peru",
                            "is_organic": True,
                            "seasonal_months": [11, 12, 1, 2],
                            "tags": ["tropical", "sweet"],
                            "image_url": "/images/kent-mango.svg",
                            "base_price_hint_eur": 1.2,
                            "attributes": {"shelf_life_days": 10, "storage": "room-temperature"},
                            "_id": "6a48056f850cca8e87c51099",
                        })
                    }
                },
            }
        },
    },
)
async def create_fruit(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.catalogue_service_url}/fruits", request, content=body,
                         headers={"content-type": "application/json"})


@app.patch(
    "/fruits/{fruit_id}",
    tags=["fruits"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({"base_price_hint_eur": 1.5})
                }
            },
        },
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_FRUIT_EXAMPLE)}},
            }
        },
    },
)
async def update_fruit(fruit_id: str, request: Request):
    body = await request.body()
    return await _proxy("PATCH", f"{settings.catalogue_service_url}/fruits/{fruit_id}", request, content=body,
                         headers={"content-type": "application/json"})


@app.delete("/fruits/{fruit_id}", status_code=204, tags=["fruits"])
async def delete_fruit(fruit_id: str, request: Request):
    return await _proxy("DELETE", f"{settings.catalogue_service_url}/fruits/{fruit_id}", request)


@app.post(
    "/fruits/{fruit_id}/approve",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_FRUIT_EXAMPLE)}},
            }
        },
    },
)
async def approve_fruit(fruit_id: str, request: Request):
    return await _proxy("POST", f"{settings.catalogue_service_url}/fruits/{fruit_id}/approve", request)


@app.post(
    "/fruits/{fruit_id}/reject",
    tags=["fruits"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_FRUIT_EXAMPLE)}},
            }
        },
    },
)
async def reject_fruit(fruit_id: str, request: Request):
    return await _proxy("POST", f"{settings.catalogue_service_url}/fruits/{fruit_id}/reject", request)


# ---- Orders (proxied to orders-service) ------------------------------------

_ORDER_EXAMPLE = {
    "id": "9c858901-8a57-4791-81fe-4c455b099324",
    "status": "confirmed",
    "total_eur": 2.95,
    "created_at": "2026-08-28T14:03:00Z",
    "items": [
        {"fruit_sku": "pink-lady-apple", "quantity": 3, "unit_price_eur": 0.65},
        {"fruit_sku": "alphonso-mango", "quantity": 1, "unit_price_eur": 1.0},
    ],
}


@app.post(
    "/orders",
    tags=["orders"],
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({
                        "items": [
                            {"fruit_sku": "pink-lady-apple", "quantity": 3},
                            {"fruit_sku": "alphonso-mango", "quantity": 1},
                        ]
                    })
                }
            },
        },
        "responses": {
            "201": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_ORDER_EXAMPLE)}},
            }
        },
    },
)
async def create_order(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.orders_service_url}/orders", request, content=body,
                         headers={"content-type": "application/json"})


@app.get(
    "/orders",
    tags=["orders"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example([_ORDER_EXAMPLE])}},
            }
        },
    },
)
async def list_orders(request: Request):
    return await _proxy("GET", f"{settings.orders_service_url}/orders", request)


@app.get(
    "/orders/{order_id}",
    tags=["orders"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_ORDER_EXAMPLE)}},
            }
        },
    },
)
async def get_order(order_id: str, request: Request):
    return await _proxy("GET", f"{settings.orders_service_url}/orders/{order_id}", request)


# ---- Comments (proxied to catalogue-service) --------------------------------

_COMMENT_EXAMPLE = {
    "_id": "66b1f0c2a1e4f2b3c4d5e6f7",
    "fruit_slug": "pink-lady-apple",
    "author": "Maria",
    "body": "So crisp and juicy, my favourite snack apple!",
    "created_at": "2026-08-28T14:03:00Z",
}


@app.get(
    "/fruits/{slug}/comments",
    tags=["comments"],
    openapi_extra={
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example([_COMMENT_EXAMPLE])}},
            }
        },
    },
)
async def list_comments(slug: str, request: Request):
    return await _proxy("GET", f"{settings.catalogue_service_url}/fruits/{slug}/comments", request)


@app.post(
    "/fruits/{slug}/comments",
    tags=["comments"],
    status_code=201,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({
                        "author": "Maria",
                        "body": "So crisp and juicy, my favourite snack apple!",
                    })
                }
            },
        },
        "responses": {
            "201": {
                "description": "Successful Response",
                "content": {"application/json": {"examples": _example(_COMMENT_EXAMPLE)}},
            }
        },
    },
)
async def add_comment(slug: str, request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.catalogue_service_url}/fruits/{slug}/comments", request,
                        content=body, headers={"content-type": "application/json"})


@app.delete("/fruits/{slug}/comments/{comment_id}", tags=["comments"])
async def delete_comment(slug: str, comment_id: str, request: Request):
    return await _proxy("DELETE", f"{settings.catalogue_service_url}/fruits/{slug}/comments/{comment_id}", request)


# ---- AI assistant (proxied to fruit-assistant-service) --------------------

@app.post(
    "/assistant/chat",
    tags=["assistant"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "examples": _example({
                        "message": "What's a good fruit for a lunchbox snack?",
                        "history": [],
                    })
                }
            },
        },
        "responses": {
            "200": {
                "description": "Successful Response",
                "content": {
                    "application/json": {
                        "examples": _example({
                            "reply": "The Pink Lady Apple is a great pick — crisp, sweet-tart, "
                            "and it holds up well without refrigeration for a few hours.",
                            "used_fallback": False,
                        })
                    }
                },
            }
        },
    },
)
async def chat(request: Request):
    body = await request.body()
    return await _proxy("POST", f"{settings.assistant_service_url}/chat", request, content=body,
                         headers={"content-type": "application/json"})
