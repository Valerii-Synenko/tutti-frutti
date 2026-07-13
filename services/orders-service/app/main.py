from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_auth
from app.database import Order, OrderItem, get_db, init_models
from app.inventory_client import inventory_client
from app.schemas import OrderCreate, OrderOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield
    await inventory_client.close()


app = FastAPI(
    title="Tutti Frutti — Orders Service",
    description="Cart & order placement. Talks to inventory-service over gRPC "
    "to validate stock and pricing before committing an order to Postgres.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "orders-service"}


@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED, tags=["orders"])
async def create_order(
    payload: OrderCreate,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    skus = [item.fruit_sku for item in payload.items]
    stock_info = {s.sku: s for s in await inventory_client.batch_get_stock(skus)}

    order = Order(user_id=user_id, status="pending", total_eur=0.0)
    total = 0.0

    for requested in payload.items:
        stock = stock_info.get(requested.fruit_sku)
        if stock is None or not stock.in_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{requested.fruit_sku}' is not available",
            )
        if stock.quantity_available < requested.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {stock.quantity_available} of '{requested.fruit_sku}' left in stock",
            )

        reservation = await inventory_client.reserve_stock(requested.fruit_sku, requested.quantity)
        if not reservation.success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not reserve '{requested.fruit_sku}': {reservation.message}",
            )

        line_total = stock.unit_price_eur * requested.quantity
        total += line_total
        order.items.append(
            OrderItem(
                fruit_sku=requested.fruit_sku,
                quantity=requested.quantity,
                unit_price_eur=stock.unit_price_eur,
            )
        )

    order.total_eur = round(total, 2)
    order.status = "confirmed"

    db.add(order)
    await db.commit()
    await db.refresh(order, attribute_names=["items"])
    return order


@app.get("/orders", response_model=list[OrderOut], tags=["orders"])
async def list_my_orders(user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
    return result.scalars().unique().all()


@app.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
async def get_order(order_id: str, user_id: str = Depends(require_auth), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
