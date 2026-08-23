"""Order schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class OrderCreate(BaseModel):
    conversation_id: uuid.UUID
    merchant_id: uuid.UUID
    customer_phone: str | None = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID | None = None
    items: list[dict]
    subtotal: float
    total: float
    rzp_order_id: str | None = None
    payment_link: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
