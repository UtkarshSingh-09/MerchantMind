"""Conversation Memory & Customer Profile Optimization Service.
Provides sliding window context management, LLM-powered summarization,
and persistent Customer Profile & Order History memory injection.
"""

import json
import logging
import uuid
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.order import Order
from app.services.groq_client import groq_client

logger = logging.getLogger(__name__)

SUMMARIZATION_SYSTEM_PROMPT = """You are a conversation memory compression engine for an AI e-commerce agent.
Your task is to summarize past messages concisely without losing vital shopping context.

Key elements to retain:
1. Customer's explicit needs, preferences, dietary constraints, occasions (e.g. birthday, anniversary).
2. Budget constraints mentioned (amount, flexible vs hard).
3. Products discussed, accepted, or rejected.
4. Stores mentioned or visited.
5. Delivery / Pickup preferences.

Output format: A concise 2-4 sentence summary bulleted context. Do NOT include greetings or fluff.
"""


async def summarize_older_messages(messages: list[dict[str, Any]]) -> str:
    """Compress older conversation turns into a dense factual summary."""
    if not messages:
        return ""

    transcript_lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if content and role in ("user", "assistant"):
            transcript_lines.append(f"{role.upper()}: {content}")

    if not transcript_lines:
        return ""

    transcript_text = "\n".join(transcript_lines)

    try:
        response = await groq_client.fast_completion(
            messages=[
                {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Summarize this conversation history:\n{transcript_text}"},
            ],
            temperature=0.0,
            max_tokens=220,
        )
        summary = (response.choices[0].message.content or "").strip()
        return summary
    except Exception as exc:
        logger.warning("Memory summarization failed, falling back to truncated transcript: %s", exc)
        return f"Previous turns covered: {transcript_lines[-3:]}"


async def build_optimized_context(
    conversation: Conversation,
    max_recent: int = 6,
) -> list[dict[str, Any]]:
    """Build a context-window optimized message list for LLM prompting."""
    raw_messages = list(conversation.messages or [])

    # Filter only valid user/assistant turns
    valid_turns = [
        m for m in raw_messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if len(valid_turns) <= max_recent + 2:
        return [
            {"role": m.get("role"), "content": m.get("content")}
            for m in valid_turns
        ]

    # Split into older and recent
    older_turns = valid_turns[:-max_recent]
    recent_turns = valid_turns[-max_recent:]

    summary_text = await summarize_older_messages(older_turns)

    optimized: list[dict[str, Any]] = []

    if summary_text:
        optimized.append({
            "role": "system",
            "content": f"📋 PREVIOUS CONVERSATION CONTEXT (Summarized from earlier turns):\n{summary_text}",
        })

    for m in recent_turns:
        optimized.append({
            "role": m.get("role"),
            "content": m.get("content"),
        })

    return optimized


async def build_customer_profile_memory(
    customer_id: uuid.UUID | None,
    db: AsyncSession,
) -> str:
    """Build a rich, structured memory context prompt for returning customers.

    Extracts:
    1. Saved delivery addresses (e.g. Home, Office, Default location)
    2. Explicit preferences (dietary, spice tolerance, preferred budget)
    3. Favorite merchants and historical ratings
    4. Past 5 orders with items and satisfaction ratings
    """
    if not customer_id:
        return ""

    try:
        # Fetch Customer record
        stmt_c = select(Customer).where(Customer.id == customer_id)
        res_c = await db.execute(stmt_c)
        customer = res_c.scalar_one_or_none()

        if not customer:
            return ""

        # Fetch recent 5 completed orders
        stmt_o = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(desc(Order.created_at))
            .limit(5)
        )
        res_o = await db.execute(stmt_o)
        recent_orders = res_o.scalars().all()

        lines = [
            "👤 RETURNING CUSTOMER PROFILE & AMBIENT MEMORY:",
            f"- Customer Name: {customer.name or 'Valued Customer'} (Phone: {customer.phone})",
            f"- Total Orders to Date: {customer.order_count} | Total Lifetime Spend: ₹{customer.total_spent:.2f}",
        ]

        # 1. Saved Addresses
        saved_addrs = customer.saved_addresses or []
        if saved_addrs:
            addr_strs = []
            for a in saved_addrs:
                label = a.get("label", "Saved")
                addr_text = a.get("address", "")
                is_def = " [DEFAULT]" if a.get("is_default") else ""
                addr_strs.append(f"  • {label}{is_def}: {addr_text}")
            lines.append("- Saved Delivery Locations:\n" + "\n".join(addr_strs))

        # 2. Preferences
        prefs = customer.preferences or {}
        if prefs:
            pref_parts = []
            if "dietary" in prefs:
                pref_parts.append(f"Dietary: {', '.join(prefs['dietary']) if isinstance(prefs['dietary'], list) else prefs['dietary']}")
            if "preferred_spice" in prefs:
                pref_parts.append(f"Spice: {prefs['preferred_spice']}")
            if "max_typical_budget" in prefs:
                pref_parts.append(f"Typical Budget: ₹{prefs['max_typical_budget']}")
            if pref_parts:
                lines.append(f"- Customer Preferences: {'; '.join(pref_parts)}")

        # 3. Favorite Merchants & Ratings
        favs = customer.favorite_merchants or []
        if favs:
            fav_strs = []
            for f in favs:
                m_name = f.get("name", "Merchant")
                last_item = f.get("last_item", "")
                rating = f.get("rating", 5)
                fav_strs.append(f"  • {m_name} (Rated {rating}/5 ⭐ — Loved '{last_item}')")
            lines.append("- Favorite Places & Past Ratings:\n" + "\n".join(fav_strs))

        # 4. Recent Order History
        if recent_orders:
            order_strs = []
            for o in recent_orders:
                item_names = [i.get("name", "Item") for i in (o.items or [])]
                order_strs.append(f"  • Order #{str(o.id)[:8]}: {', '.join(item_names)} (Total ₹{o.total:.2f}, Status: {o.status.value})")
            lines.append("- Recent Order History:\n" + "\n".join(order_strs))

        lines.append(
            "DIRECTIVE FOR AGENT:\n"
            "1. Proactively reference their positive past experiences when relevant (e.g. 'Last time you loved the Manchurian from Beijing Bites...').\n"
            "2. Offer to reorder favorite dishes or suggest similar high-rated alternatives within their budget.\n"
            "3. If they confirm ordering, pre-fill their default saved address automatically."
        )

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("Failed to build customer profile memory: %s", exc)
        return ""
