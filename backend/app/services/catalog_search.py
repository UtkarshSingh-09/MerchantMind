"""Catalog search, cross-merchant discovery, and filtering service."""

import uuid
from typing import Any
from sqlalchemy import select, or_, func, desc
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
        cat_clean = category.strip()
        cat_stem = cat_clean.rstrip("s") if cat_clean.lower().endswith("s") and not cat_clean.lower().endswith("ss") else cat_clean
        stmt = stmt.where(
            or_(
                Product.category.ilike(f"%{cat_clean}%"),
                Product.category.ilike(f"%{cat_stem}%"),
            )
        )

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
    "choclate": "chocolate",
    "choclte": "chocolate",
    "veggie": "veg",
    "pastries": "pastry",
    "pastry": "pastries",
    "manchurian": "manchurian",
    "dosa": "dosa",
    "dosaa": "dosa",
    "dose": "dosa",
    "dhosa": "dosa",
    "idli": "idli",
    "biryani": "biryani",
    "biriyani": "biryani",
    "briyani": "biryani",
    "truffles": "truffle",
    "truffel": "truffle",
    "trufle": "truffle",
    "filetrr": "filter",
    "filtre": "filter",
    "fliter": "filter",
    "filterr": "filter",
    "coffe": "coffee",
    "cofee": "coffee",
    "kaapi": "coffee",
    "kapi": "coffee",
    "benidosa": "benne",
    "benedosa": "benne",
    "bennedosa": "benne",
    "benne": "benne",
    "piza": "pizza",
    "pzza": "pizza",
    "pizaa": "pizza",
    "burgir": "burger",
    "burgr": "burger",
    "paneer": "paneer",
    "panir": "paneer",
    "margheritta": "margherita",
    "margharita": "margherita",
    "margarita": "margherita",
    "pizzas": "pizza",
    "burgers": "burger",
    "dosas": "dosa",
    "coffees": "coffee",
    "idlis": "idli",
    "cakes": "cake",
    "biryanis": "biryani",
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
    """Search products across ALL active merchants in the city with name-prioritized relevance matching."""
    stmt = (
        select(Product, Merchant.name.label("merchant_name"), Merchant.id.label("m_id"))
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Product.in_stock == True, Merchant.is_active == True)
    )

    if category:
        cat_clean = category.strip()
        cat_stem = cat_clean.rstrip("s") if cat_clean.lower().endswith("s") and not cat_clean.lower().endswith("ss") else cat_clean
        stmt = stmt.where(
            or_(
                Product.category.ilike(f"%{cat_clean}%"),
                Product.category.ilike(f"%{cat_stem}%"),
            )
        )

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    tokens = _normalize_tokens(query) if query and query.strip() else []

    if tokens:
        # Require at least one token to match in Product.name OR Category (prevents description false-positives like 'rice cakes')
        name_or_cat_conditions = []
        for t in tokens:
            name_or_cat_conditions.append(Product.name.ilike(f"%{t}%"))
            name_or_cat_conditions.append(Product.category.ilike(f"%{t}%"))
        stmt = stmt.where(or_(*name_or_cat_conditions))

    stmt = stmt.order_by(desc(Product.rating)).limit(max(limit * 30, 200))
    result = await db.execute(stmt)
    rows = result.all()

    # Score and rank matched products
    scored_items = []
    query_lower = query.lower().strip() if query else ""

    FOOD_ANCHORS = {
        "burger", "pizza", "dosa", "coffee", "cake", "biryani", "ice cream",
        "pastry", "shawarma", "sandwich", "roll", "nachos", "noodles", "pasta", "chaat"
    }
    query_anchors = [a for a in FOOD_ANCHORS if a in query_lower]

    for row in rows:
        p_name = row.Product.name.lower()
        p_cat = (row.Product.category or "").lower()
        
        score = 0.0
        # Exact full phrase match in name gets highest priority
        if query_lower and query_lower in p_name:
            score += 100.0
        
        # Token match scoring
        token_matches = 0
        for tok in tokens:
            if tok in p_name:
                score += 30.0
                token_matches += 1
            elif tok in p_cat:
                score += 15.0

        # Multi-token synergy bonus
        if len(tokens) > 1 and token_matches == len(tokens):
            score += 50.0

        # Food-anchor alignment bonus / cross-cuisine penalty
        if query_anchors:
            if any(qa in p_name or qa in p_cat for qa in query_anchors):
                score += 60.0
            elif any(other in p_name or other in p_cat for other in FOOD_ANCHORS if other not in query_anchors):
                score -= 80.0

        # Rating boost
        if row.Product.rating:
            score += float(row.Product.rating)

        # Budget match boost
        if max_price is not None and row.Product.price <= max_price:
            score += 10.0

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
            "rating": getattr(row.Product, "rating", 4.5) or 4.5,
            "is_veg": getattr(row.Product, "is_veg", True),
            "is_trending": bool((getattr(row.Product, "rating", 4.5) or 4.5) >= 4.7),
            "badge": (
                "🔥 Trending"
                if (getattr(row.Product, "rating", 4.5) or 4.5) >= 4.7
                else ("⭐ Best Seller" if (getattr(row.Product, "rating", 4.5) or 4.5) >= 4.5 else "")
            ),
        }
        for row in top_rows
    ]



async def search_with_alternatives(
    db: AsyncSession,
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    is_veg: bool | None = None,
    limit: int = 6,
) -> dict[str, Any]:
    """Three-Tier Knowledge Funnel:
    Tier 1: Exact / high-relevance token matching across all city stores
    Tier 2: Distinguish in-budget matches from over-budget matches
    Tier 3: When exact matches exceed budget or are missing, pull top-rated in-budget alternatives in the same category
    """
    # 1. First search with NO max_price to see if the exact product exists anywhere in Bangalore
    all_exact_matches = await search_all_merchants_catalog(
        db, query=query, category=category, min_price=min_price, max_price=None, limit=limit * 2
    )

    detected_category = category
    if not detected_category and all_exact_matches:
        detected_category = all_exact_matches[0].get("category")

    in_budget_exact: list[dict[str, Any]] = []
    over_budget_exact: list[dict[str, Any]] = []

    for item in all_exact_matches:
        if is_veg is True and item.get("is_veg") is False:
            continue
        price = float(item["price"])
        if max_price is not None and price > max_price:
            diff = price - max_price
            item["over_budget_by"] = diff
            over_budget_exact.append(item)
        else:
            in_budget_exact.append(item)

    # 2. If in-budget matches are fewer than 3, find top in-budget alternatives in the same category
    category_alternatives: list[dict[str, Any]] = []
    if (len(in_budget_exact) < 2) and (detected_category or query):
        cat_to_search = detected_category
        if not cat_to_search and query:
            q_lower = query.lower()
            if "cake" in q_lower or "pastry" in q_lower or "truffle" in q_lower:
                cat_to_search = "Cakes"
            elif "biryani" in q_lower:
                cat_to_search = "Biryani"
            elif "coffee" in q_lower or "tea" in q_lower or "shake" in q_lower:
                cat_to_search = "Beverages"
            elif "dosa" in q_lower or "idli" in q_lower:
                cat_to_search = "South Indian"
            elif "burger" in q_lower:
                cat_to_search = "Burgers"
            elif "pizza" in q_lower:
                cat_to_search = "Pizza"
            elif "ice cream" in q_lower or "sundae" in q_lower:
                cat_to_search = "Desserts"
            elif "manchurian" in q_lower or "noodles" in q_lower or "fried rice" in q_lower:
                cat_to_search = "Chinese"
            elif "chaat" in q_lower or "puri" in q_lower or "bhel" in q_lower:
                cat_to_search = "Street Food"

        if cat_to_search:
            cat_clean = cat_to_search.strip()
            cat_stem = cat_clean.rstrip("s") if cat_clean.lower().endswith("s") and not cat_clean.lower().endswith("ss") else cat_clean
            alt_stmt = (
                select(Product, Merchant.name.label("merchant_name"), Merchant.id.label("m_id"))
                .join(Merchant, Product.merchant_id == Merchant.id)
                .where(
                    Product.in_stock == True,
                    Merchant.is_active == True,
                    or_(
                        Product.category.ilike(f"%{cat_clean}%"),
                        Product.category.ilike(f"%{cat_stem}%"),
                    ),
                )
            )
            if max_price is not None:
                alt_stmt = alt_stmt.where(Product.price <= max_price)
            if is_veg is True:
                alt_stmt = alt_stmt.where(Product.is_veg == True)

            alt_stmt = alt_stmt.order_by(Product.rating.desc().nullslast(), Product.price.asc()).limit(limit)
            alt_res = await db.execute(alt_stmt)
            alt_rows = alt_res.all()

            existing_ids = {item["id"] for item in in_budget_exact}
            for row in alt_rows:
                if str(row.Product.id) not in existing_ids:
                    category_alternatives.append({
                        "id": str(row.Product.id),
                        "merchant_id": str(row.m_id),
                        "merchant_name": row.merchant_name,
                        "name": row.Product.name,
                        "price": row.Product.price,
                        "category": row.Product.category or "General",
                        "description": row.Product.description or "",
                        "tags": row.Product.tags or [],
                        "image_url": row.Product.image_url or "",
                        "rating": getattr(row.Product, "rating", 4.5) or 4.5,
                        "is_veg": getattr(row.Product, "is_veg", True),
                        "is_trending": bool((getattr(row.Product, "rating", 4.5) or 4.5) >= 4.7),
                        "badge": (
                            "🔥 Trending"
                            if (getattr(row.Product, "rating", 4.5) or 4.5) >= 4.7
                            else ("⭐ Best Seller" if (getattr(row.Product, "rating", 4.5) or 4.5) >= 4.5 else "")
                        ),
                    })

    # 3. Build human-shopkeeper reasoning explanation
    explanation_parts = []
    if over_budget_exact and not in_budget_exact:
        top_ob = over_budget_exact[0]
        budget_str = f"your ₹{max_price:.0f} budget" if max_price is not None else "your budget"
        explanation_parts.append(
            f"The exact item '{top_ob['name']}' is available from {top_ob['merchant_name']} at ₹{top_ob['price']:.0f} (₹{top_ob.get('over_budget_by', 0):.0f} above {budget_str})."
        )
        if category_alternatives:
            under_str = f"under ₹{max_price:.0f} " if max_price is not None else ""
            explanation_parts.append(
                f"However, we have {len(category_alternatives)} wonderful {under_str}{cat_to_search or 'category'} options with great customer ratings!"
            )
    elif in_budget_exact:
        if max_price is not None:
            explanation_parts.append(
                f"Found {len(in_budget_exact)} matching options right within your ₹{max_price:.0f} budget."
            )
        else:
            explanation_parts.append(
                f"Found {len(in_budget_exact)} matching options across Bangalore stores."
            )
    elif not all_exact_matches and category_alternatives:
        explanation_parts.append(
            f"We don't have an exact match for '{query}', but here are {len(category_alternatives)} top-rated alternatives in Bangalore!"
        )

    return {
        "exact_matches": in_budget_exact[:limit],
        "over_budget_matches": over_budget_exact[:3],
        "alternatives": category_alternatives[:limit],
        "has_exact_match": len(in_budget_exact) > 0,
        "is_over_budget": len(over_budget_exact) > 0 and len(in_budget_exact) == 0,
        "detected_category": detected_category,
        "explanation": " ".join(explanation_parts),
    }


async def search_by_occasion(
    db: AsyncSession,
    occasion: str,
    budget: float | None = None,
    people_count: int | None = None,
    is_veg: bool | None = None,
) -> dict[str, Any]:
    """Curate food combos and party platters tailored for specific occasions.
    Handles birthday parties, office lunches, date nights, tea time snacks, and family feasts.
    """
    import re
    occ_lower = occasion.lower()

    # Extract people count if mentioned in query, e.g. "for 10 people", "10 pax", "serves 5"
    if people_count is None:
        p_match = re.search(r"(\d+)\s*(?:people|persons|guests|pax|folks|friends|colleagues)", occ_lower)
        if p_match:
            people_count = int(p_match.group(1))
        else:
            people_count = 4

    # Extract budget if not explicitly provided
    if budget is None:
        b_match = re.search(r"(?:under|below|budget|within|max)\s*(?:₹|rs\.?|inr)?\s*(\d+)", occ_lower)
        if b_match:
            budget = float(b_match.group(1))

    # Detect theme and categories
    if any(k in occ_lower for k in ["birthday", "anniversary", "party", "celebration", "celebrate"]):
        theme = "Birthday & Celebration"
        target_cats = ["Cakes", "Pastries", "Beverages", "Desserts"]
        description = f"Festive party combo for {people_count} guests including celebratory cake and treats."
    elif any(k in occ_lower for k in ["office", "lunch", "meeting", "work", "corporate", "colleague"]):
        theme = "Office & Team Lunch"
        target_cats = ["Biryani", "North Indian", "South Indian", "Beverages"]
        description = f"Convenient, crowd-pleasing office lunch spread for {people_count} people."
    elif any(k in occ_lower for k in ["date", "romantic", "couple", "two"]):
        theme = "Romantic Dinner for Two"
        people_count = 2
        target_cats = ["Pizza", "Pastries", "Beverages", "Cakes"]
        description = "Intimate gourmet dinner combo with artisan mains and indulgent dessert."
    elif any(k in occ_lower for k in ["tea", "snack", "evening", "chai", "coffee", "break"]):
        theme = "Tea Time & Evening Snacks"
        target_cats = ["Pastries", "Breads", "Beverages", "Street Food"]
        description = f"Light, crisp evening refreshments and beverages for {people_count} people."
    else:
        theme = "Family Feast & Gathering"
        target_cats = ["Biryani", "North Indian", "South Indian", "Desserts"]
        description = f"Wholesome feast designed to delight a gathering of {people_count} people."

    # Fetch top products matching target categories
    stmt = (
        select(Product, Merchant.name.label("merchant_name"), Merchant.id.label("m_id"))
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Product.in_stock == True, Merchant.is_active == True)
    )
    if is_veg is True:
        stmt = stmt.where(Product.is_veg == True)

    cat_filters = [Product.category.ilike(f"%{c}%") for c in target_cats]
    stmt = stmt.where(or_(*cat_filters)).order_by(Product.rating.desc().nullslast()).limit(25)

    res = await db.execute(stmt)
    candidate_rows = res.all()

    # Assemble combo items
    selected_items = []
    accumulated_cost = 0.0
    seen_merchants = set()

    for row in candidate_rows:
        p = row.Product
        # Portion rule
        is_cake = "cake" in (p.category or "").lower() or "cake" in p.name.lower()
        qty = 1 if is_cake else max(1, people_count // 3)
        item_cost = p.price * qty

        if budget is not None and (accumulated_cost + item_cost) > budget and len(selected_items) >= 2:
            continue

        selected_items.append({
            "product_id": str(p.id),
            "name": p.name,
            "category": p.category or "Special",
            "merchant_name": row.merchant_name,
            "merchant_id": str(row.m_id),
            "unit_price": p.price,
            "quantity": qty,
            "subtotal": round(item_cost, 2),
            "rating": getattr(p, "rating", 4.7) or 4.7,
            "is_veg": getattr(p, "is_veg", True),
            "badge": "🔥 Trending" if (getattr(p, "rating", 4.5) or 4.5) >= 4.7 else "⭐ Best Seller",
        })
        accumulated_cost += item_cost
        seen_merchants.add(row.merchant_name)
        if len(selected_items) >= 4:
            break

    per_person_cost = round(accumulated_cost / max(1, people_count), 2)

    return {
        "occasion_theme": theme,
        "people_count": people_count,
        "description": description,
        "target_budget": budget,
        "within_budget": budget is None or accumulated_cost <= budget,
        "total_combo_cost": round(accumulated_cost, 2),
        "cost_per_person": per_person_cost,
        "curated_items": selected_items,
        "suggested_stores": list(seen_merchants),
        "summary": f"Curated {len(selected_items)} items for {people_count} people totaling ₹{accumulated_cost:.0f} (₹{per_person_cost:.0f}/person).",
    }


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
