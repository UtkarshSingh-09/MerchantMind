"""Intelligent, Context-Aware Upsell and Cross-Sell Engine with budget bounding."""

import uuid
import logging
from typing import Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product

logger = logging.getLogger(__name__)

# Category and product association pairings for cross-selling & upselling
CATEGORY_UPSELL_RULES: dict[str, list[dict[str, Any]]] = {
    "cakes": [
        {"target_category": "Party Supplies", "keywords": ["candle", "balloon", "sparkler", "party"], "reason": "Pairs perfectly with cakes for birthday celebrations and parties"},
        {"target_category": "Pastries", "keywords": ["truffle", "pastry", "cupcake"], "reason": "Delicious bite-sized treats to complement your cake"},
        {"target_category": "Beverages", "keywords": ["coffee", "cold brew", "shake"], "reason": "Refreshing beverages to serve alongside cake"},
    ],
    "pastries": [
        {"target_category": "Beverages", "keywords": ["coffee", "latte", "cappuccino", "hot chocolate", "tea"], "reason": "Freshly brewed artisan coffee or beverage pairs delightfully with pastries"},
        {"target_category": "Combos", "keywords": ["combo", "box", "pack"], "reason": "Upgrade to an assorted pastry gift box for higher savings"},
    ],
    "breads": [
        {"target_category": "Beverages", "keywords": ["soup", "coffee", "tea"], "reason": "Warm drinks pair wonderfully with freshly baked artisan bread"},
        {"target_category": "Pastries", "keywords": ["croissant", "danish"], "reason": "Add a sweet morning pastry to your bakery order"},
    ],
    "beverages": [
        {"target_category": "Pastries", "keywords": ["croissant", "cookie", "muffin", "brownie"], "reason": "Freshly baked bakery snacks to enjoy with your beverage"},
        {"target_category": "Cakes", "keywords": ["slice", "pastry", "cake"], "reason": "Indulgent dessert slice to enjoy with coffee"},
    ],
}


async def get_upsell_suggestions(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    cart_items: list[dict[str, Any]],
    budget_remaining: float | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Generate smart, budget-bounded upsell and cross-sell suggestions based on cart contents."""
    if not cart_items:
        # If cart is empty, suggest bestsellers/popular items
        stmt = select(Product).where(
            and_(Product.merchant_id == merchant_id, Product.in_stock == True)
        ).order_by(Product.price.asc()).limit(limit)
        res = await db.execute(stmt)
        products = list(res.scalars().all())
        return [
            {
                "product_id": str(p.id),
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "image_url": p.image_url,
                "reasoning": f"Store favorite '{p.name}' for only ₹{p.price}",
            }
            for p in products
        ]

    # Collect categories and names of products in cart to avoid duplicate suggestions
    cart_product_ids = {str(i.get("product_id")) for i in cart_items}
    cart_categories = {str(i.get("category", "")).lower() for i in cart_items}

    # If category not present in cart item dict, fetch from DB
    if not any(cart_categories):
        p_ids = [uuid.UUID(i["product_id"]) for i in cart_items if i.get("product_id")]
        if p_ids:
            p_stmt = select(Product).where(Product.id.in_(p_ids))
            p_res = await db.execute(p_stmt)
            cart_categories = {p.category.lower() for p in p_res.scalars().all() if p.category}

    # Find matched upsell pairing rules
    matched_rules: list[dict[str, Any]] = []
    for cat in cart_categories:
        for rule_cat, rules in CATEGORY_UPSELL_RULES.items():
            if rule_cat in cat:
                matched_rules.extend(rules)

    if not matched_rules:
        # Default fallback rule: suggest Party Supplies or Beverages
        matched_rules = CATEGORY_UPSELL_RULES.get("cakes", [])

    # Query catalog for matching items
    suggestions: list[dict[str, Any]] = []
    all_products_stmt = select(Product).where(
        and_(
            Product.merchant_id == merchant_id,
            Product.in_stock == True,
            Product.id.notin_([uuid.UUID(pid) for pid in cart_product_ids if pid and pid != "None"]),
        )
    )
    all_res = await db.execute(all_products_stmt)
    available_products = list(all_res.scalars().all())

    for rule in matched_rules:
        target_cat = rule.get("target_category", "").lower()
        keywords = rule.get("keywords", [])
        rule_reason = rule.get("reason", "Complementary recommendation")

        for p in available_products:
            # Check budget cap
            if budget_remaining is not None and p.price > budget_remaining:
                continue

            p_cat = (p.category or "").lower()
            p_name = p.name.lower()
            p_desc = (p.description or "").lower()

            matches_cat = target_cat in p_cat
            matches_kw = any(kw in p_name or kw in p_desc for kw in keywords)

            if matches_cat or matches_kw:
                if not any(s["product_id"] == str(p.id) for s in suggestions):
                    budget_note = f" (fits in remaining budget: ₹{budget_remaining:.0f})" if budget_remaining else ""
                    suggestions.append({
                        "product_id": str(p.id),
                        "name": p.name,
                        "price": p.price,
                        "category": p.category,
                        "image_url": p.image_url,
                        "reasoning": f"{rule_reason} — only ₹{p.price:.0f}{budget_note}",
                    })
                    if len(suggestions) >= limit:
                        break
        if len(suggestions) >= limit:
            break

    # If still need suggestions, fill with any product within budget
    if len(suggestions) < limit:
        for p in available_products:
            if budget_remaining is not None and p.price > budget_remaining:
                continue
            if not any(s["product_id"] == str(p.id) for s in suggestions):
                suggestions.append({
                    "product_id": str(p.id),
                    "name": p.name,
                    "price": p.price,
                    "category": p.category,
                    "image_url": p.image_url,
                    "reasoning": f"Popular add-on: {p.name} (₹{p.price:.0f})",
                })
                if len(suggestions) >= limit:
                    break

    logger.info("Generated %d upsell suggestions for merchant %s", len(suggestions), merchant_id)
    return suggestions
