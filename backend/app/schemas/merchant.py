"""Merchant schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class MerchantCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    description: str | None = None
    rzp_key_id: str | None = None
    rzp_key_secret: str | None = None
    whatsapp_number: str | None = None


class MerchantUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    description: str | None = None
    rzp_key_id: str | None = None
    rzp_key_secret: str | None = None
    whatsapp_number: str | None = None


class MerchantResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    description: str | None = None
    whatsapp_number: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
