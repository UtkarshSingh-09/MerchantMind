"""Catalog search and filtering service."""

import uuid
from typing import Any
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product


async def search_products(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True,
    limit: int = 10,
) -> list[Product]:
    """Search products in a merchant's catalog with flexible filters."""
    stmt = select(Product).where(Product.merchant_id == merchant_id)

    if in_stock_only:
        stmt = stmt.where(Product.in_stock == True)

    if category:
        stmt = stmt.where(Product.category.ilike(f"%{category.strip()}%"))

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    if query:
        search_term = f"%{query.strip()}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.category.ilike(search_term),
            )
        )

    stmt = stmt.order_by(Product.price.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_product_by_id(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    product_id: uuid.UUID,
) -> Product | None:
    """Fetch single product by ID for a merchant."""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.merchant_id == merchant_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_merchant_catalog_summary(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Get summarized catalog for system prompt / agent baseline knowledge."""
    products = await search_products(db, merchant_id, limit=limit, in_stock_only=True)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "price": p.price,
            "category": p.category or "General",
            "description": p.description or "",
            "tags": p.tags or [],
            "image_url": p.image_url or "",
        }
        for p in products
    ]
