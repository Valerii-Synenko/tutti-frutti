import re
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderItemCreate(BaseModel):
    fruit_sku: str = Field(min_length=1, description="Fruit slug, e.g. 'pink-lady-apple'")
    quantity: int = Field(gt=0, le=100)


class ContactIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(
        pattern=r"^\+?[0-9][0-9 ()-]{6,19}$",
        description="Contact phone, digits with optional leading '+', spaces, dashes or parentheses",
        examples=["+385 91 234 5678"],
    )


class ShippingAddressIn(BaseModel):
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(pattern=r"^[A-Za-z0-9 -]{3,10}$")
    country: str = Field(min_length=2, max_length=100)


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def card_brand(digits: str) -> str:
    if digits.startswith("4"):
        return "visa"
    if re.match(r"^(5[1-5]|2[2-7])", digits):
        return "mastercard"
    if re.match(r"^3[47]", digits):
        return "amex"
    return "card"


class PaymentIn(BaseModel):
    """Card details for the (simulated) payment. Only the brand and last four
    digits are ever stored — the full number and CVC are discarded after the
    charge is approved."""

    cardholder_name: str = Field(min_length=1, max_length=120)
    card_number: str = Field(description="13-19 digits, spaces allowed; must pass the Luhn check")
    expiry: str = Field(pattern=r"^(0[1-9]|1[0-2])/[0-9]{2}$", description="MM/YY, not in the past")
    cvc: str = Field(pattern=r"^[0-9]{3,4}$")

    @field_validator("card_number")
    @classmethod
    def _valid_card_number(cls, value: str) -> str:
        digits = value.replace(" ", "")
        if not re.fullmatch(r"[0-9]{13,19}", digits) or not _luhn_ok(digits):
            raise ValueError("Invalid card number")
        return digits

    @field_validator("expiry")
    @classmethod
    def _not_expired(cls, value: str) -> str:
        month, year = int(value[:2]), 2000 + int(value[3:])
        today = date.today()
        if (year, month) < (today.year, today.month):
            raise ValueError("Card has expired")
        return value


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    contact: ContactIn
    shipping_address: ShippingAddressIn
    payment: PaymentIn


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fruit_sku: str
    quantity: int
    unit_price_eur: float


class ContactOut(BaseModel):
    full_name: str
    phone: str


class ShippingAddressOut(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str


class PaymentOut(BaseModel):
    status: str = Field(description="'paid' once the charge is approved")
    card_brand: str
    card_last4: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    total_eur: float
    created_at: datetime
    items: list[OrderItemOut]
    # Null for orders placed before checkout collected these details.
    contact: ContactOut | None = None
    shipping_address: ShippingAddressOut | None = None
    payment: PaymentOut | None = None


class SalesSummaryItem(BaseModel):
    fruit_sku: str
    quantity_sold: int
    revenue_eur: float
    orders_count: int


class SalesSummaryOut(BaseModel):
    items: list[SalesSummaryItem]
    total_quantity_sold: int
    total_revenue_eur: float
