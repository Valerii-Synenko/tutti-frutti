import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    total_eur: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Checkout details. Nullable because orders placed before checkout existed
    # don't have them. Only the card brand + last four digits are kept.
    contact_name: Mapped[str | None] = mapped_column(String(120))
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    ship_street: Mapped[str | None] = mapped_column(String(200))
    ship_city: Mapped[str | None] = mapped_column(String(100))
    ship_postal_code: Mapped[str | None] = mapped_column(String(10))
    ship_country: Mapped[str | None] = mapped_column(String(100))
    payment_status: Mapped[str | None] = mapped_column(String(16))
    card_brand: Mapped[str | None] = mapped_column(String(16))
    card_last4: Mapped[str | None] = mapped_column(String(4))

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    @property
    def contact(self) -> dict | None:
        if self.contact_name is None:
            return None
        return {"full_name": self.contact_name, "phone": self.contact_phone}

    @property
    def shipping_address(self) -> dict | None:
        if self.ship_street is None:
            return None
        return {
            "street": self.ship_street,
            "city": self.ship_city,
            "postal_code": self.ship_postal_code,
            "country": self.ship_country,
        }

    @property
    def payment(self) -> dict | None:
        if self.payment_status is None:
            return None
        return {"status": self.payment_status, "card_brand": self.card_brand, "card_last4": self.card_last4}


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"))
    fruit_sku: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_eur: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# create_all only creates missing tables, it never adds columns to an existing
# one — so columns added after the first release are added here, idempotently.
_ADDED_ORDER_COLUMNS = {
    "contact_name": "VARCHAR(120)",
    "contact_phone": "VARCHAR(32)",
    "ship_street": "VARCHAR(200)",
    "ship_city": "VARCHAR(100)",
    "ship_postal_code": "VARCHAR(10)",
    "ship_country": "VARCHAR(100)",
    "payment_status": "VARCHAR(16)",
    "card_brand": "VARCHAR(16)",
    "card_last4": "VARCHAR(4)",
}


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "postgresql":
            for column, column_type in _ADDED_ORDER_COLUMNS.items():
                await conn.execute(text(f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {column} {column_type}"))
