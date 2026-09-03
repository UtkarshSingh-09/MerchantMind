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


SYNONYMS = {
    "belgium": "belgian",
    "choc": "chocolate",
    "veggie": "veg",
    "pastries": "pastry",
    "pastry": "pastries",
    "manchurian": "manchurian",
    "dosa": "dosa",
    "idli": "idli",
    "biryani": "biryani",
    "truffles": "truffle",
}


def _normalize_tokens(query_str: str) -> list[str]:
    import re
    cleaned = re.sub(r"[^\w\s]", " ", query_str.lower())
    raw = [w for w in cleaned.split() if len(w) >= 3 and not w.isdigit()]
    return [SYNONYMS.get(w, w) for w in raw]


async def search_all_merchants_catalog(
    db: AsyncSession,
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search products across ALL active merchants in the city with multi-token relevance matching."""
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
        # If budget is specified, allow a small 35% margin for exact matches (e.g. ₹650 for ₹500 budget)
        stmt = stmt.where(Product.price <= (max_price * 1.35))

    if query and query.strip():
        tokens = _normalize_tokens(query)
        if tokens:
            token_conditions = []
            for t in tokens:
                token_conditions.append(Product.name.ilike(f"%{t}%"))
                token_conditions.append(Product.description.ilike(f"%{t}%"))
                token_conditions.append(Product.category.ilike(f"%{t}%"))
            stmt = stmt.where(or_(*token_conditions))

    stmt = stmt.order_by(Product.price.asc()).limit(limit * 2)
    result = await db.execute(stmt)
    rows = result.all()

    # Score and rank matched products
    query_tokens = set(_normalize_tokens(query)) if query else set()
    scored_items = []
    for row in rows:
        p_name = row.Product.name.lower()
        p_desc = (row.Product.description or "").lower()
        p_cat = (row.Product.category or "").lower()
        
        score = 0
        if query and query.lower().strip() in p_name:
            score += 10
        for tok in query_tokens:
            if tok in p_name:
                score += 5
            elif tok in p_desc:
                score += 2
            elif tok in p_cat:
                score += 3
        
        # Prioritize in-budget items
        if max_price and row.Product.price <= max_price:
            score += 4

        scored_items.append((score, row))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    top_rows = [item[1] for item in scored_items[:limit]]

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
        for row in top_rows
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


_MERCHANT_SUMMARY_CACHE: list[dict[str, Any]] | None = None
_CACHE_TIMESTAMP: float = 0.0
_CACHE_TTL: float = 60.0  # 60 seconds TTL


async def get_all_merchants_summary(db: AsyncSession) -> list[dict[str, Any]]:
    """Get all active merchants with product counts and price range via a single SQL query (0-2ms)."""
    global _MERCHANT_SUMMARY_CACHE, _CACHE_TIMESTAMP
    import time
    now = time.time()
    if _MERCHANT_SUMMARY_CACHE is not None and (now - _CACHE_TIMESTAMP) < _CACHE_TTL:
        return _MERCHANT_SUMMARY_CACHE

    stmt = (
        select(
            Merchant.id,
            Merchant.name,
            Merchant.description,
            func.count(Product.id).label("product_count"),
            func.coalesce(func.min(Product.price), 0.0).label("min_price"),
            func.coalesce(func.max(Product.price), 0.0).label("max_price"),
        )
        .outerjoin(Product, (Product.merchant_id == Merchant.id) & (Product.in_stock == True))
        .where(Merchant.is_active == True)
        .group_by(Merchant.id, Merchant.name, Merchant.description)
        .order_by(Merchant.name.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    summaries = [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description or "",
            "product_count": r.product_count,
            "categories": [],
            "price_range": f"₹{r.min_price:.0f} — ₹{r.max_price:.0f}",
        }
        for r in rows
    ]
    _MERCHANT_SUMMARY_CACHE = summaries
    _CACHE_TIMESTAMP = now
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
