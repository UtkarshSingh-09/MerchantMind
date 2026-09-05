"""Order schemas for requests and responses."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class OrderCreate(BaseModel):
    conversation_id: uuid.UUID
    merchant_id: uuid.UUID
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    callback_url: str | None = None
    fulfillment_mode: str | None = "delivery"  # "delivery" or "pickup"
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    pickup_time: str | None = None
    items: list[dict[str, Any]] | None = None



class OrderResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    items: list[dict[str, Any]]
    subtotal: float
    total: float
    fulfillment_mode: str | None = "delivery"
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    pickup_time: str | None = None
    rzp_order_id: str | None = None
    rzp_payment_id: str | None = None
    rzp_payment_link_id: str | None = None
    payment_link: str | None = None
    status: str
    audit_trail: list[dict[str, Any]] | None = None
    sibling_orders: list[dict[str, Any]] | None = None
    merchant_name: str | None = None
    created_at: datetime
    paid_at: datetime | None = None
    rzp_key_id: str | None = None

    model_config = {"from_attributes": True}


class OrderStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    total: float
    rzp_order_id: str | None = None
    rzp_payment_id: str | None = None
    payment_link: str | None = None
    paid_at: datetime | None = None
    rzp_key_id: str | None = None

    model_config = {"from_attributes": True}


class PaymentLinkResponse(BaseModel):
    order_id: uuid.UUID
    payment_link: str
    amount: float
    status: str


class MultiOrderCreate(BaseModel):
    conversation_id: uuid.UUID
    items: list[dict[str, Any]]
    fulfillment_mode: str | None = "delivery"
    delivery_address: str | None = None
    delivery_latitude: float | None = None
    delivery_longitude: float | None = None
    pickup_time: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    callback_url: str | None = None


class MultiOrderResponse(BaseModel):
    primary_order_id: uuid.UUID
    sibling_order_ids: list[uuid.UUID]
    orders: list[OrderResponse]
    total: float
    payment_link: str | None = None
    rzp_order_id: str | None = None
    rzp_key_id: str | None = None
    fulfillment_mode: str = "delivery"
    message: str
