"""Product model — items in a merchant's catalog."""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    price_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, default=10, nullable=True)

    @property
    def authoritative_price_paise(self) -> int:
        if self.price_paise is not None:
            return self.price_paise
        return int(round(self.price * 100))


    # Schema.org JSON-LD representation (auto-generated)
    schema_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    merchant = relationship("Merchant", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

    def to_schema_org(self) -> dict:
        """Generate Schema.org/JSON-LD Product representation."""
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": self.name,
            "description": self.description or "",
            "offers": {
                "@type": "Offer",
                "price": self.price,
                "priceCurrency": "INR",
                "availability": (
                    "https://schema.org/InStock"
                    if self.in_stock
                    else "https://schema.org/OutOfStock"
                ),
            },
            "category": self.category or "",
            "image": self.image_url or "",
            "identifier": str(self.id),
        }
