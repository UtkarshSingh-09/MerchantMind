"""Chat schemas for request/response validation."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    merchant_id: uuid.UUID | None = None  # None = Discovery Mode (cross-merchant)
    conversation_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    message: str
    customer_phone: str | None = None
    cart_items: list[dict[str, Any]] | None = None


class ProductRecommendation(BaseModel):
    product_id: uuid.UUID
    name: str
    price: float
    description: str | None = None
    image_url: str | None = None
    category: str | None = None
    merchant_name: str | None = None
    merchant_id: uuid.UUID | None = None
    reasoning: str  # Why the agent recommended this product


class CartItem(BaseModel):
    product_id: uuid.UUID
    name: str
    price: float
    quantity: int = 1
    merchant_id: uuid.UUID | None = None
    merchant_name: str | None = None

    model_config = {"extra": "allow"}


class CartUpdatePayload(BaseModel):
    items: list[CartItem]


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    order_id: str | None = None
    merchant_id: uuid.UUID | None = None
    merchant_name: str | None = None
    message: str
    recommendations: list[ProductRecommendation] | None = None
    cart: list[CartItem] | None = None
    cart_total: float | None = None
    action: str | None = None  # "recommend", "cart_update", "checkout", "chat"
    payment_link: str | None = None
    agent_reasoning: list[dict[str, Any]] | None = None


class MessageItem(BaseModel):
    role: str
    content: str
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID | None = None
    channel: str
    status: str
    messages: list[dict[str, Any]]
    cart: dict[str, Any]
    agent_reasoning: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
