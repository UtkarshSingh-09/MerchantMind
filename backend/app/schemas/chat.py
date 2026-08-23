"""Chat schemas."""

import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    merchant_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    message: str
    customer_phone: str | None = None


class ProductRecommendation(BaseModel):
    product_id: uuid.UUID
    name: str
    price: float
    description: str | None = None
    image_url: str | None = None
    reasoning: str  # Why the agent recommended this


class CartItem(BaseModel):
    product_id: uuid.UUID
    name: str
    price: float
    quantity: int = 1


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str
    recommendations: list[ProductRecommendation] | None = None
    cart: list[CartItem] | None = None
    cart_total: float | None = None
    action: str | None = None  # "search", "recommend", "upsell", "checkout", "confirm"
    payment_link: str | None = None
