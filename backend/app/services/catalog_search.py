"""Catalog search, cross-merchant discovery, and filtering service."""

import uuid
from typing import Any
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.models.merchant import Merchant


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
    """Search products in a specific merchant's catalog with flexible filters."""
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


async def search_all_merchants_catalog(
    db: AsyncSession,
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search products across ALL active merchants in the city (Discovery Mode).

    Returns products with their merchant name attached for cross-store comparison.
    """
    stmt = (
        select(Product, Merchant.name.label("merchant_name"), Merchant.id.label("m_id"))
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Product.in_stock == True, Merchant.is_active == True)
    )

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
    rows = result.all()

    return [
        {
            "id": str(row.Product.id),
            "merchant_id": str(row.m_id),
            "merchant_name": row.merchant_name,
            "name": row.Product.name,
            "price": row.Product.price,
            "category": row.Product.category or "General",
            "description": row.Product.description or "",
            "tags": row.Product.tags or [],
            "image_url": row.Product.image_url or "",
        }
        for row in rows
    ]


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


async def get_product_by_id_any_merchant(
    db: AsyncSession,
    product_id: uuid.UUID,
) -> Product | None:
    """Fetch a product by ID regardless of merchant (for discovery mode add-to-cart)."""
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_merchants_summary(db: AsyncSession) -> list[dict[str, Any]]:
    """Get all active merchants with product counts and category breakdown.

    Used to populate the Discovery Mode system prompt so the AI knows
    what stores are available in the city.
    """
    merchants_stmt = select(Merchant).where(Merchant.is_active == True)
    merchants_res = await db.execute(merchants_stmt)
    merchants = list(merchants_res.scalars().all())

    summaries = []
    for m in merchants:
        # Get product count and category breakdown
        count_stmt = select(func.count(Product.id)).where(
            Product.merchant_id == m.id, Product.in_stock == True
        )
        count_res = await db.execute(count_stmt)
        product_count = count_res.scalar() or 0

        cat_stmt = (
            select(Product.category, func.count(Product.id).label("cnt"))
            .where(Product.merchant_id == m.id, Product.in_stock == True)
            .group_by(Product.category)
        )
        cat_res = await db.execute(cat_stmt)
        categories = [
            {"name": row.category or "General", "count": row.cnt}
            for row in cat_res.all()
        ]

        # Get price range
        price_stmt = (
            select(func.min(Product.price), func.max(Product.price))
            .where(Product.merchant_id == m.id, Product.in_stock == True)
        )
        price_res = await db.execute(price_stmt)
        price_row = price_res.one_or_none()
        min_price = (price_row[0] if price_row and price_row[0] is not None else 0.0)
        max_price = (price_row[1] if price_row and price_row[1] is not None else 0.0)

        summaries.append({
            "id": str(m.id),
            "name": m.name,
            "description": m.description or "",
            "product_count": product_count,
            "categories": categories,
            "price_range": f"₹{min_price:.0f} — ₹{max_price:.0f}",
        })

    return summaries


async def get_merchant_catalog_summary(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    limit: int = 40,
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
