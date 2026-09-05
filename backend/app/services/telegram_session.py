"""Telegram Session Manager — maps incoming Telegram chat & sender to Customer and Conversation."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


async def get_default_merchant(db: AsyncSession) -> Merchant | None:
    """Fetch the default primary active merchant for fallback association."""
    stmt = select(Merchant).where(Merchant.is_active == True).order_by(Merchant.created_at.asc()).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def get_or_create_telegram_session(
    db: AsyncSession,
    chat_id: int | str,
    user_info: dict[str, Any] | None = None,
    merchant_id: uuid.UUID | None = None,
) -> tuple[Conversation, Customer, Merchant | None]:
    """Resolve or create the Customer, Conversation, and Merchant for an incoming Telegram message.
    
    If no merchant is pre-locked, merchant is returned as None to enable city-wide DiscoveryAgent.
    Once an item/store is chosen, the conversation is locked to that merchant.
    """
    user_info = user_info or {}
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or user_info.get("username") or f"Telegram User {chat_id}"
    username = user_info.get("username")
    tg_identifier = f"tg_{chat_id}"

    # Default platform merchant to satisfy Customer foreign key if needed
    default_merchant = await get_default_merchant(db)

    # 1. Resolve or create Customer
    cust_stmt = select(Customer).where(Customer.phone == tg_identifier)
    cust_res = await db.execute(cust_stmt)
    customer = cust_res.scalar_one_or_none()

    if not customer:
        if not default_merchant:
            raise ValueError("No active merchant in system for customer account creation.")
        customer = Customer(
            merchant_id=default_merchant.id,
            name=full_name,
            phone=tg_identifier,
            email=f"{username}@telegram.org" if username else None,
        )
        db.add(customer)
        await db.flush()
        logger.info("Created new customer %s for Telegram chat %s (%s)", customer.id, chat_id, full_name)
    elif customer.name != full_name and full_name:
        customer.name = full_name
        await db.flush()

    # 2. Resolve active Telegram Conversation (within last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    conv_stmt = select(Conversation).where(
        and_(
            Conversation.customer_id == customer.id,
            Conversation.channel == "telegram",
            Conversation.status == "active",
            Conversation.updated_at >= cutoff,
        )
    ).order_by(Conversation.updated_at.desc()).limit(1)

    conv_res = await db.execute(conv_stmt)
    conversation = conv_res.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            merchant_id=merchant_id,  # None by default for city-wide discovery
            customer_id=customer.id,
            channel="telegram",
            status="active",
            messages=[],
            cart={"items": [], "total": 0.0},
            agent_reasoning=[],
        )
        db.add(conversation)
        await db.flush()
        logger.info("Started new Telegram conversation %s for customer %s (city-wide discovery mode)", conversation.id, customer.id)

    # 3. Resolve active merchant if conversation is locked
    active_merchant = None
    target_mid = conversation.merchant_id or merchant_id
    if target_mid:
        m_stmt = select(Merchant).where(Merchant.id == target_mid)
        m_res = await db.execute(m_stmt)
        active_merchant = m_res.scalar_one_or_none()

    return conversation, customer, active_merchant


async def handle_telegram_order_management(
    db: AsyncSession,
    customer: Customer,
    chat_id: int | str,
    user_text: str,
    conversation: Conversation | None = None,
) -> bool:
    """Check and handle order tracking, address updates, and fulfillment switching directly."""
    import re
    from sqlalchemy import or_
    from app.models.order import Order, OrderStatus
    from app.services.order_service import get_order_tracking_data
    from app.services.telegram_service import telegram_service

    async def get_latest_order() -> Order | None:
        where_cond = (Order.customer_id == customer.id)
        if conversation:
            where_cond = or_(where_cond, Order.conversation_id == conversation.id)
        stmt = select(Order).where(where_cond).order_by(Order.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    text_lower = user_text.strip().lower()

    # 1. Check for live order tracking requests
    is_tracking_cmd = (
        text_lower.startswith("track")
        or "where is my order" in text_lower
        or "order status" in text_lower
        or "track live order" in text_lower
    )
    if is_tracking_cmd:
        order = await get_latest_order()

        if not order:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="🔍 <b>No active orders found.</b>\n\nCraving something delicious? Tell me what you'd like to order across Bangalore!",
                parse_mode="HTML",
            )
            return True

        tracking = await get_order_tracking_data(db, order.id)
        if not tracking:
            await telegram_service.send_message(
                chat_id=chat_id,
                text="⚠️ Unable to fetch tracking data at this moment.",
                parse_mode="HTML",
            )
            return True

        pct = tracking.get("live_progress_percentage", 25)
        filled_bars = int(pct // 10)
        empty_bars = 10 - filled_bars
        bar_str = "█" * filled_bars + "░" * empty_bars

        items_str = ", ".join([f"{i.get('quantity', 1)}x {i.get('name')}" for i in (order.items or [])])
        mode_label = "🛵 Doorstep Delivery" if not tracking.get("is_pickup") else "🏪 Counter Pickup"
        addr_label = order.delivery_address or "Pending customer location"

        msg = (
            f"📍 <b>Live Order Tracking</b> — <code>#{str(order.id)[:8]}</code>\n\n"
            f"🏪 <b>Store:</b> {tracking['store_name']}\n"
            f"🛍️ <b>Items:</b> {items_str}\n"
            f"📊 <b>Status:</b> <b>{tracking['current_stage']}</b>\n"
            f"<code>[{bar_str}] {pct}%</code>\n\n"
            f"⏱️ <b>Remaining ETA:</b> ~<b>{tracking['remaining_eta_minutes']} mins</b>\n"
            f"📋 <b>Fulfillment:</b> {mode_label}\n"
        )
        if tracking.get("is_pickup"):
            msg += (
                f"📍 <b>Store Address:</b> {tracking['store_address']}\n"
                f"🔑 <b>Pickup OTP:</b> <code>{tracking['pickup_otp']}</code>\n"
            )
        else:
            msg += (
                f"🛵 <b>Delivery Partner:</b> {tracking['driver_name']} ({tracking['driver_vehicle']})\n"
                f"🏠 <b>Delivering To:</b> {addr_label}\n"
            )

        buttons = [
            {"text": "🔄 Refresh Status", "callback_data": f"track order {str(order.id)[:8]}"},
            {"text": "🛵 Change Address", "callback_data": "share delivery address"},
            {"text": "🏪 Switch to Self-Pickup" if not tracking.get("is_pickup") else "🛵 Switch to Delivery",
             "callback_data": "switch to pickup" if not tracking.get("is_pickup") else "switch to delivery"},
        ]
        await telegram_service.send_interactive_buttons(chat_id, msg, buttons, parse_mode="HTML")
        return True

    # 2. Check for switching to Self-Pickup
    if text_lower in ["switch to pickup", "pickup", "self pickup", "store pickup", "self-pickup"]:
        order = await get_latest_order()
        if order:
            order.fulfillment_mode = "pickup"
            await db.commit()
            tracking = await get_order_tracking_data(db, order.id)
            otp = tracking.get("pickup_otp", "7821") if tracking else "7821"
            store_name = tracking.get("store_name", "the store") if tracking else "the store"
            store_addr = tracking.get("store_address", "Bangalore") if tracking else "Bangalore"
            prep_time = tracking.get("prep_time_minutes", 15) if tracking else 15

            pickup_msg = (
                f"🏪 <b>Fulfillment Updated to Self-Pickup!</b>\n\n"
                f"Your order <code>#{str(order.id)[:8]}</code> will be freshly packed and ready at <b>{store_name}</b>!\n\n"
                f"📍 <b>Store Address:</b> {store_addr}\n"
                f"🔑 <b>Pickup OTP:</b> <code>{otp}</code>\n"
                f"⏱️ <b>Ready for Pickup in:</b> ~{prep_time} mins\n\n"
                f"<i>Simply show this OTP at the counter to collect your order!</i>"
            )
            buttons = [
                {"text": "📍 Track Live Order", "callback_data": f"track order {str(order.id)[:8]}"},
                {"text": "🛵 Switch back to Delivery", "callback_data": "switch to delivery"},
            ]
            await telegram_service.send_interactive_buttons(chat_id, pickup_msg, buttons, parse_mode="HTML")
            return True

    # 3. Check for switching to Delivery
    if text_lower in ["switch to delivery", "delivery", "home delivery", "doorstep delivery", "switch back to delivery"]:
        order = await get_latest_order()
        if order:
            order.fulfillment_mode = "delivery"
            await db.commit()
            msg = (
                f"🛵 <b>Switched to Doorstep Delivery!</b>\n\n"
                f"Please reply with your delivery address or area in Bangalore (e.g. <i>'Frazer Town, Coles Road, Flat 4B'</i>) so our rider can deliver to your doorstep!"
            )
            await telegram_service.send_message(chat_id, msg, parse_mode="HTML")
            return True

    # 4. Check for address input
    address_keywords = ["road", "street", "layout", "nagar", "town", "floor", "apt", "flat", "block", "cross", "main", "bengaluru", "bangalore", "near", "opposite", "lane"]
    is_address_prompt = text_lower in ["share delivery address", "enter delivery address", "change address"]
    has_address_keywords = any(kw in text_lower for kw in address_keywords) and len(user_text.split()) >= 2
    is_explicit_address = text_lower.startswith("deliver to") or text_lower.startswith("address:") or text_lower.startswith("my address is")

    if is_address_prompt:
        await telegram_service.send_message(
            chat_id=chat_id,
            text="📍 <b>Please reply with your delivery address</b> in Bangalore (e.g. <i>'Frazer Town, Coles Road, Apt 4B'</i> or <i>'Indiranagar 100ft Road'</i>).",
            parse_mode="HTML",
        )
        return True

    if has_address_keywords or is_explicit_address:
        order = await get_latest_order()
        if order:
            clean_addr = re.sub(r"^(deliver to|my address is|address is|address:)\s*", "", user_text, flags=re.IGNORECASE).strip()
            order.delivery_address = clean_addr
            order.fulfillment_mode = "delivery"
            await db.commit()

            tracking = await get_order_tracking_data(db, order.id)
            eta = tracking.get("remaining_eta_minutes", 25) if tracking else 25
            driver = tracking.get("driver_name", "Ramesh K.") if tracking else "Ramesh K."
            vehicle = tracking.get("driver_vehicle", "TVS Jupiter • KA-03-HA-8821") if tracking else ""

            msg = (
                f"📍 <b>Delivery Address Confirmed!</b>\n\n"
                f"🏠 <b>Delivering to:</b> {clean_addr}\n"
                f"🛵 <b>Assigned Rider:</b> {driver} ({vehicle})\n"
                f"⏱️ <b>Live ETA:</b> ~{eta} mins\n\n"
                f"Your order <code>#{str(order.id)[:8]}</code> is being prepared hot and fresh!"
            )
            buttons = [
                {"text": "📍 Track Live Order", "callback_data": f"track order {str(order.id)[:8]}"},
                {"text": "🏪 Switch to Self-Pickup", "callback_data": "switch to pickup"},
            ]
            await telegram_service.send_interactive_buttons(chat_id, msg, buttons, parse_mode="HTML")
            return True

    return False
