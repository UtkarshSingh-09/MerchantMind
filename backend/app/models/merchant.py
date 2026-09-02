"""Merchant model — represents a business using MerchantMind."""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Razorpay credentials (test mode)
    rzp_key_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rzp_key_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # WhatsApp
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Store Location (for Haversine real ETA math)
    store_latitude: Mapped[float | None] = mapped_column(nullable=True)
    store_longitude: Mapped[float | None] = mapped_column(nullable=True)
    store_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Authentication & Security
    api_key_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="merchant", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="merchant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Merchant(id={self.id}, name='{self.name}')>"
