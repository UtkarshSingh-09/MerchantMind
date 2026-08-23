"""Campaign model — re-engagement campaigns for dormant customers."""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )

    # Campaign details
    campaign_type: Mapped[str] = mapped_column(String(50), default="re-engagement")
    message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    offer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Razorpay Payment Link
    rzp_payment_link: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, converted, expired
    converted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="campaigns")
    customer = relationship("Customer")

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, type='{self.campaign_type}', status='{self.status}')>"
