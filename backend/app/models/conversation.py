"""Conversation model — tracks chat sessions between customer and merchant agent."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )

    # Channel: "web" or "whatsapp"
    channel: Mapped[str] = mapped_column(String(20), default="web")

    # Messages: list of {role, content, timestamp, metadata}
    messages: Mapped[list] = mapped_column(JSONB, default=list)

    # Current cart state
    cart: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Agent reasoning logs
    agent_reasoning: Mapped[list] = mapped_column(JSONB, default=list)

    # Status: active, completed, abandoned
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    orders = relationship("Order", back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, channel='{self.channel}', status='{self.status}')>"
