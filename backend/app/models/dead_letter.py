"""Webhook Dead Letter Queue (DLQ) Model — Tracks failed webhooks for retry and auditing."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WebhookDeadLetter(Base):
    __tablename__ = "webhook_dead_letters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="razorpay")  # "razorpay", "pos", "whatsapp"
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # "pending", "retried", "resolved", "failed"
    last_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<WebhookDeadLetter(id={self.id}, event='{self.event_type}', status='{self.status}', retries={self.retry_count})>"
