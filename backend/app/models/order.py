"""Order model — tracks purchases and Razorpay payment status."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PAYMENT_CREATED = "payment_created"
    PAYMENT_LINK_SENT = "payment_link_sent"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )

    # Order details
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal_paise: Mapped[int | None] = mapped_column(nullable=True)
    total_paise: Mapped[int | None] = mapped_column(nullable=True)

    @property
    def authoritative_total_paise(self) -> int:
        if self.total_paise is not None:
            return self.total_paise
        return int(round(self.total * 100))

    @property
    def authoritative_subtotal_paise(self) -> int:
        if self.subtotal_paise is not None:
            return self.subtotal_paise
        return int(round(self.subtotal * 100))

    # Razorpay
    rzp_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rzp_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rzp_payment_link_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING
    )

    # Fulfillment (Online Delivery vs Offline Store Pickup)
    fulfillment_mode: Mapped[str | None] = mapped_column(
        String(20), default="delivery", nullable=True
    )
    delivery_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_latitude: Mapped[float | None] = mapped_column(nullable=True)
    delivery_longitude: Mapped[float | None] = mapped_column(nullable=True)
    pickup_time: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Audit trail (list of decision logs)
    audit_trail: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    conversation = relationship("Conversation", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, total={self.total}, status='{self.status}')>"
