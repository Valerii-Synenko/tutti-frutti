from typing import Annotated, Any, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# This is exactly the case that motivates using MongoDB for the catalogue:
# different fruits have genuinely different attribute shapes (tropical fruits
# care about ripening_climate, berries care about shelf_life_days, etc).
# We model the common fields explicitly and let `attributes` hold the
# fruit-specific, schema-flexible extras as free-form JSON.

PyObjectId = Annotated[str, BeforeValidator(str)]


class FruitBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=120, description="URL-friendly unique identifier, e.g. 'pink-lady-apple'")
    description: str = Field(default="", max_length=2000)
    origin: str = Field(default="", description="Country or region of origin")
    is_organic: bool = False
    seasonal_months: list[int] = Field(default_factory=list, description="1-12, months when in season")
    tags: list[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    base_price_hint_eur: float = Field(default=0.0, ge=0, description="Reference price; authoritative price comes from inventory-service")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Schema-flexible, fruit-specific attributes")


class FruitCreate(FruitBase):
    pass


class FruitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    origin: Optional[str] = None
    is_organic: Optional[bool] = None
    seasonal_months: Optional[list[int]] = None
    tags: Optional[list[str]] = None
    image_url: Optional[str] = None
    base_price_hint_eur: Optional[float] = None
    attributes: Optional[dict[str, Any]] = None


class FruitOut(FruitBase):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id")
