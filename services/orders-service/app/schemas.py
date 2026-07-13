import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    fruit_sku: str = Field(min_length=1, description="Fruit slug, e.g. 'pink-lady-apple'")
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fruit_sku: str
    quantity: int
    unit_price_eur: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    total_eur: float
    created_at: datetime
    items: list[OrderItemOut]
