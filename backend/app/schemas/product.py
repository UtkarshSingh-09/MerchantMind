"""Product schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    in_stock: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category: str | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    in_stock: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    description: str | None = None
    price: float
    category: str | None = None
    tags: list[str] | None = None
    image_url: str | None = None
    in_stock: bool
    created_at: datetime

    model_config = {"from_attributes": True}
