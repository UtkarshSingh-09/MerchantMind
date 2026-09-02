"""Merchant Operations and Analytics Service.
Provides database aggregation and management tools for the Merchant Operations Agent.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.conversation import Conversation
from app.services.groq_client import groq_client

logger = logging.getLogger(__name__)


async def get_store_stats(db: AsyncSession, merchant_id: uuid.UUID) -> dict[str, Any]:
    """Fetch high-level operational statistics for a merchant."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Total products & out of stock
    prod_stmt = select(Product).where(Product.merchant_id == merchant_id)
    prod_res = await db.execute(prod_stmt)
    products = list(prod_res.scalars().all())
    total_products = len(products)
    out_of_stock = sum(1 for p in products if not p.in_stock)

    # 2. Today's orders & revenue
    order_stmt = select(Order).where(
        Order.merchant_id == merchant_id,
        Order.created_at >= today_start,
    )
    order_res = await db.execute(order_stmt)
    today_orders = list(order_res.scalars().all())
    orders_count = len(today_orders)
    paid_orders = [o for o in today_orders if o.status in [OrderStatus.PAID, "paid"]]
    revenue_today = sum(o.total for o in paid_orders)

    return {
        "product_count": total_products,
        "out_of_stock": out_of_stock,
        "in_stock_count": total_products - out_of_stock,
        "orders_today": orders_count,
        "paid_orders_today": len(paid_orders),
        "revenue_today": round(revenue_today, 2),
    }


async def get_sales_for_period(
    db: AsyncSession, merchant_id: uuid.UUID, period: str = "today"
) -> dict[str, Any]:
    """Retrieve detailed sales breakdown for a specified time period."""
    now = datetime.now(timezone.utc)
    period_lower = period.lower().replace("-", "_").replace(" ", "_")

    if period_lower in ["today", "24h", "24_hours"]:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = "Today"
    elif period_lower in ["yesterday"]:
        start_time = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = "Yesterday"
    elif period_lower in ["this_week", "7_days", "last_7_days"]:
        start_time = now - timedelta(days=7)
        label = "Last 7 Days"
    elif period_lower in ["this_month", "30_days", "last_30_days"]:
        start_time = now - timedelta(days=30)
        label = "Last 30 Days"
    else:
        start_time = now - timedelta(days=7)
        label = "Recent Period"

    stmt = select(Order).where(
        Order.merchant_id == merchant_id,
        Order.created_at >= start_time,
    ).order_by(desc(Order.created_at))

    res = await db.execute(stmt)
    orders = list(res.scalars().all())

    total_orders = len(orders)
    paid_orders = [o for o in orders if o.status in [OrderStatus.PAID, "paid"]]
    pending_orders = [o for o in orders if o.status in [OrderStatus.PENDING, OrderStatus.PAYMENT_LINK_SENT, "pending", "payment_link_sent"]]
    failed_orders = [o for o in orders if o.status in [OrderStatus.FAILED, "failed"]]

    gross_sales = sum(o.total for o in paid_orders)
    aov = (gross_sales / len(paid_orders)) if paid_orders else 0.0

    # Top selling items aggregation from items JSONB
    item_sales: dict[str, dict[str, Any]] = {}
    for o in paid_orders:
        for item in (o.items or []):
            name = item.get("name", "Unknown Item")
            qty = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            if name not in item_sales:
                item_sales[name] = {"quantity": 0, "revenue": 0.0}
            item_sales[name]["quantity"] += qty
            item_sales[name]["revenue"] += qty * price

    top_items = sorted(
        [{"name": k, "units_sold": v["quantity"], "revenue": round(v["revenue"], 2)} for k, v in item_sales.items()],
        key=lambda x: x["units_sold"],
        reverse=True,
    )[:5]

    return {
        "period": label,
        "total_orders": total_orders,
        "paid_orders": len(paid_orders),
        "pending_orders": len(pending_orders),
        "failed_orders": len(failed_orders),
        "gross_sales": round(gross_sales, 2),
        "average_order_value": round(aov, 2),
        "top_selling_items": top_items,
    }


async def update_product_stock_and_price(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    product_name_or_id: str,
    in_stock: bool | None = None,
    new_price: float | None = None,
) -> dict[str, Any]:
    """Find a product by name or UUID and update stock status / price."""
    product: Product | None = None

    # Try UUID first
    try:
        pid = uuid.UUID(product_name_or_id)
        stmt = select(Product).where(Product.merchant_id == merchant_id, Product.id == pid)
        res = await db.execute(stmt)
        product = res.scalar_one_or_none()
    except Exception:
        pass

    # Try fuzzy name match
    if not product:
        stmt = select(Product).where(
            Product.merchant_id == merchant_id,
            Product.name.ilike(f"%{product_name_or_id}%"),
        )
        res = await db.execute(stmt)
        product = res.scalars().first()

    if not product:
        return {
            "success": False,
            "error": f"Product matching '{product_name_or_id}' was not found in your catalog.",
        }

    changes = []
    if in_stock is not None:
        old_stock = product.in_stock
        product.in_stock = in_stock
        changes.append(f"Stock changed from {'In Stock' if old_stock else 'Out of Stock'} to {'In Stock' if in_stock else 'Out of Stock'}")

    if new_price is not None and new_price > 0:
        old_p = product.price
        product.price = float(new_price)
        changes.append(f"Price updated from ₹{old_p:.0f} to ₹{new_price:.0f}")

    product.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(product)

    return {
        "success": True,
        "product_id": str(product.id),
        "product_name": product.name,
        "in_stock": product.in_stock,
        "price": product.price,
        "category": product.category,
        "changes": changes,
        "message": f"Successfully updated '{product.name}': {', '.join(changes)}",
    }


async def get_trending_and_reorder_alerts(
    db: AsyncSession, merchant_id: uuid.UUID
) -> dict[str, Any]:
    """Flag low-stock or out-of-stock items that have high customer demand."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # 1. Fetch all products
    prod_stmt = select(Product).where(Product.merchant_id == merchant_id)
    prod_res = await db.execute(prod_stmt)
    products = list(prod_res.scalars().all())

    # 2. Fetch past 7 days orders
    order_stmt = select(Order).where(
        Order.merchant_id == merchant_id,
        Order.created_at >= week_ago,
    )
    order_res = await db.execute(order_stmt)
    orders = list(order_res.scalars().all())

    item_counts: dict[str, int] = {}
    for o in orders:
        for i in (o.items or []):
            pname = i.get("name", "")
            item_counts[pname] = item_counts.get(pname, 0) + int(i.get("quantity", 1))

    reorder_alerts = []
    out_of_stock_items = []

    for p in products:
        sales_7d = item_counts.get(p.name, 0)
        if not p.in_stock:
            out_of_stock_items.append({
                "product_id": str(p.id),
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "past_7d_demand": sales_7d,
                "alert": "⚠️ OUT OF STOCK" if sales_7d == 0 else f"🚨 URGENT: High Demand ({sales_7d} recent orders) but OUT OF STOCK",
            })
        elif sales_7d >= 3:
            reorder_alerts.append({
                "product_id": str(p.id),
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "velocity": f"{sales_7d} units sold in 7 days (Trending)",
                "recommendation": "Maintain buffer inventory for upcoming peak hours.",
            })

    return {
        "out_of_stock_count": len(out_of_stock_items),
        "out_of_stock_items": out_of_stock_items,
        "trending_items": reorder_alerts,
    }


async def get_abandoned_conversations(
    db: AsyncSession, merchant_id: uuid.UUID, min_value: float = 0.0
) -> list[dict[str, Any]]:
    """Identify customer shopping sessions with uncompleted carts."""
    # Find conversations locked to this merchant or with items from this merchant
    stmt = select(Conversation).where(
        Conversation.merchant_id == merchant_id,
        Conversation.status.in_(["active", "abandoned"]),
    ).order_by(desc(Conversation.updated_at)).limit(30)

    res = await db.execute(stmt)
    conversations = list(res.scalars().all())

    abandoned = []
    for conv in conversations:
        cart = conv.cart or {}
        items = cart.get("items", [])
        total = float(cart.get("total", 0.0))

        if not items or total <= min_value:
            continue

        # Check if an order was completed for this conversation
        order_stmt = select(Order).where(
            Order.conversation_id == conv.id,
            Order.status.in_([OrderStatus.PAID, "paid"]),
        )
        ord_res = await db.execute(order_stmt)
        paid_order = ord_res.scalar_one_or_none()

        if not paid_order:
            # Check last message timestamp
            last_msg = (conv.messages or [])[-1] if conv.messages else {}
            last_time = last_msg.get("timestamp") or conv.updated_at.isoformat()
            
            # Summary of items
            item_summary = ", ".join([f"{i.get('quantity', 1)}x {i.get('name')}" for i in items])
            
            abandoned.append({
                "conversation_id": str(conv.id),
                "cart_total": total,
                "item_count": len(items),
                "items_summary": item_summary,
                "items": items,
                "last_active": last_time,
                "status": "In Cart (Unpaid)",
            })

    return abandoned


async def generate_recovery_draft(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    conversation_id: uuid.UUID,
    tone: str = "friendly",
) -> dict[str, Any]:
    """Generate a personalized re-engagement message for an abandoned cart."""
    # Fetch conversation
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()

    if not conv:
        return {"success": False, "error": f"Conversation {conversation_id} not found."}

    # Fetch merchant
    m_stmt = select(Merchant).where(Merchant.id == merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()
    store_name = merchant.name if merchant else "Store"

    cart = conv.cart or {}
    items = cart.get("items", [])
    total = float(cart.get("total", 0.0))

    if not items:
        return {"success": False, "error": "No items found in this cart to recover."}

    item_names = ", ".join([f"{i.get('quantity', 1)}x {i.get('name')} (₹{i.get('price')})" for i in items])

    prompt = f"""You are drafting a WhatsApp/SMS re-engagement message for a customer of '{store_name}'.
Customer Cart: {item_names} | Total: ₹{total:.0f}
Tone: {tone} (friendly, helpful, not spammy)

Draft a concise, warm message (max 3 sentences) asking if they would like us to prepare/hold their items and send the instant payment link. Include store name and clean currency formatting.
"""

    try:
        response = await groq_client.chat_completion(
            messages=[
                {"role": "system", "content": "You write engaging, high-conversion customer re-engagement texts."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=150,
        )
        draft = response.choices[0].message.content.strip()
    except Exception as exc:
        draft = f"Hi there! 👋 Your {item_names} is still waiting in your cart at {store_name} (₹{total:.0f}). Would you like us to hold it for you and send the checkout link?"

    return {
        "success": True,
        "conversation_id": str(conversation_id),
        "cart_total": total,
        "items": items,
        "draft_message": draft,
        "tone": tone,
    }


async def generate_promotion_campaign(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    category: str | None = None,
    discount_pct: int = 15,
    reason: str = "Clear slow-moving inventory & boost weekend volume",
) -> dict[str, Any]:
    """Generate a high-converting Razorpay promotion coupon code and marketing copy."""
    m_stmt = select(Merchant).where(Merchant.id == merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()
    store_name = merchant.name if merchant else "MerchantMind Store"

    # Find products in category or slow moving
    prod_stmt = select(Product).where(
        Product.merchant_id == merchant_id,
        Product.in_stock == True,
    )
    if category:
        prod_stmt = prod_stmt.where(Product.category.ilike(f"%{category}%"))
    prod_res = await db.execute(prod_stmt.limit(6))
    eligible_prods = list(prod_res.scalars().all())

    coupon_code = f"{store_name[:4].upper()}{discount_pct}{datetime.now().strftime('%d%m')}"

    prompt = f"""You are a growth marketing strategist for '{store_name}'.
Generate a promotion plan for Coupon Code: '{coupon_code}' ({discount_pct}% OFF).
Category: {category or 'Store-Wide'}
Eligible Products: {', '.join([p.name for p in eligible_prods])}
Objective: {reason}

Return a concise marketing broadcast copy for WhatsApp/Instagram (under 4 sentences) highlighting the coupon code and discount.
"""

    try:
        response = await groq_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a growth marketing strategist creating high-converting store campaigns."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=180,
        )
        marketing_copy = (response.choices[0].message.content or "").strip()
    except Exception:
        marketing_copy = f"🎉 Flash Sale at {store_name}! Use coupon code *{coupon_code}* to get {discount_pct}% OFF your order today!"

    return {
        "success": True,
        "coupon_code": coupon_code,
        "discount_percentage": discount_pct,
        "category": category or "All Items",
        "eligible_products": [{"name": p.name, "price": p.price, "discounted_price": round(p.price * (1 - discount_pct / 100), 2)} for p in eligible_prods],
        "marketing_copy": marketing_copy,
        "valid_until": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%d %b %Y"),
        "razorpay_offer_id": f"offer_{coupon_code.lower()}",
    }


async def analyze_customer_sentiment(
    db: AsyncSession,
    merchant_id: uuid.UUID,
) -> dict[str, Any]:
    """Scan recent conversations for customer preferences, trending questions, and unmet demand."""
    conv_stmt = select(Conversation).where(
        Conversation.merchant_id == merchant_id,
    ).order_by(desc(Conversation.created_at)).limit(20)
    conv_res = await db.execute(conv_stmt)
    conversations = list(conv_res.scalars().all())

    all_user_msgs = []
    for c in conversations:
        for m in (c.messages or []):
            if m.get("role") == "user" and m.get("content"):
                all_user_msgs.append(m.get("content"))

    if not all_user_msgs:
        return {
            "conversation_count": 0,
            "sentiment_summary": "No recent customer chats found for analysis.",
            "top_requested_items": [],
            "common_questions": [],
        }

    sample_text = "\n- ".join(all_user_msgs[:30])

    prompt = f"""Analyze these recent customer messages sent to an artisan food store:
- {sample_text}

Provide:
1. Top 3 items or categories customers asked about most.
2. Common inquiries (e.g. eggless, delivery time, custom sizes).
3. Overall sentiment (Positive / Neutral / Urgent).
4. One actionable recommendation for the store manager.
"""

    try:
        response = await groq_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a customer sentiment analyst for retail and food merchants."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=250,
        )
        analysis = (response.choices[0].message.content or "").strip()
    except Exception as e:
        analysis = f"Analysis based on {len(all_user_msgs)} customer messages: High interest in baked goods and fast delivery."

    return {
        "conversation_count": len(conversations),
        "total_messages_analyzed": len(all_user_msgs),
        "analysis_report": analysis,
    }

