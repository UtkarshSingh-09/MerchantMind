"""Campaign model for proactive re-engagement and targeted promotional offers."""

import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, func
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

    campaign_type: Mapped[str] = mapped_column(String(50), default="re_engagement")  # re_engagement, birthday, seasonal
    offer: Mapped[str] = mapped_column(String(500), nullable=False)
    message_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    rzp_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="sent")  # draft, sent, delivered, failed

    converted: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    converted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    merchant = relationship("Merchant")
    customer = relationship("Customer")

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, type='{self.campaign_type}', converted={self.converted})>"
