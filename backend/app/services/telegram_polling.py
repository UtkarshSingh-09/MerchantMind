"""Telegram Long-Polling Worker — enables seamless local development and testing without ngrok or public IP."""

import asyncio
import logging
from typing import Any
import httpx

from app.config import settings
from app.database import async_session
from app.services.telegram_service import telegram_service
from app.services.telegram_session import get_or_create_telegram_session
from app.agents.agent_router import agent_router

logger = logging.getLogger(__name__)


async def process_telegram_update(data: dict[str, Any]) -> None:
    """Process a single Telegram update dict identically to the webhook handler."""
    message_obj = data.get("message")
    callback_query = data.get("callback_query")

    chat_id = None
    user_info = None
    user_text = ""

    if callback_query:
        from_user = callback_query.get("from", {})
        msg = callback_query.get("message", {})
        chat_id = msg.get("chat", {}).get("id") or from_user.get("id")
        user_info = from_user
        user_text = callback_query.get("data", "")
    elif message_obj:
        chat_id = message_obj.get("chat", {}).get("id")
        user_info = message_obj.get("from", {})
        user_text = message_obj.get("text", "").strip()

    if not chat_id or not user_text:
        return

    print(f"📩 [Telegram Bot] Received from chat {chat_id}: '{user_text}'", flush=True)
    logger.info("Telegram Poller received message from chat %s: '%s'", chat_id, user_text)
    await telegram_service.send_chat_action(chat_id, "typing")

    if user_text.lower() in ["/start", "/help"]:
        welcome_text = (
            "🙏 <b>Welcome to MerchantMind Bangalore!</b>\n\n"
            "I am your autonomous AI shopping concierge across <b>214 verified Bangalore stores</b>.\n\n"
            "Tell me what you're craving or your budget, for example:\n"
            "• <i>\"Truffle cake under ₹600\"</i>\n"
            "• <i>\"Ghee roast masala dosa under ₹200\"</i>\n"
            "• <i>\"Filter coffee in Indiranagar\"</i>\n\n"
            "You can add items to your cart and checkout directly with <b>Razorpay</b>!"
        )
        quick_buttons = [
            {"text": "🍰 Truffle Cakes", "callback_data": "Truffle cake under 600"},
            {"text": "🥞 Benne Dosa", "callback_data": "Ghee masala dosa under 200"},
            {"text": "☕ Filter Coffee", "callback_data": "Filter coffee"},
            {"text": "🛒 View Cart", "callback_data": "view cart"},
        ]
        await telegram_service.send_interactive_buttons(chat_id, welcome_text, quick_buttons)
        return

    async with async_session() as db:
        try:
            conversation, customer, merchant = await get_or_create_telegram_session(
                db=db,
                chat_id=chat_id,
                user_info=user_info,
            )

            from app.services.telegram_session import handle_telegram_order_management
            handled = await handle_telegram_order_management(
                db=db,
                customer=customer,
                chat_id=chat_id,
                user_text=user_text,
                conversation=conversation,
            )
            if handled:
                return

            agent_res = await agent_router.route_customer_message(
                db=db,
                merchant=merchant,
                conversation=conversation,
                user_message=user_text,
            )
            await db.commit()

            buttons = []
            if agent_res.recommendations:
                for r in agent_res.recommendations[:3]:
                    store_short = r.merchant_name.split()[0] if r.merchant_name else "Store"
                    store_label = f" from {store_short}"
                    cb_data = f"Add 1 {r.name[:25]}{store_label}"[:55]
                    buttons.append({
                        "text": f"🛒 {store_short} — {r.name[:16]} (₹{r.price:.0f})",
                        "callback_data": cb_data,
                    })

            if agent_res.cart_total and agent_res.cart_total > 0:
                buttons.append({"text": f"💳 Checkout & Pay (₹{agent_res.cart_total:.0f})", "callback_data": "checkout"})
                buttons.append({"text": "🛒 View Cart", "callback_data": "view cart"})
            elif buttons:
                buttons.append({"text": "💳 Checkout & Pay", "callback_data": "checkout"})

            if buttons and not agent_res.payment_link:
                await telegram_service.send_interactive_buttons(
                    chat_id=chat_id,
                    text=agent_res.message,
                    buttons=buttons,
                    parse_mode="HTML",
                )
            else:
                await telegram_service.send_message(
                    chat_id=chat_id,
                    text=agent_res.message,
                    parse_mode="HTML",
                )

            if agent_res.payment_link:
                await telegram_service.send_payment_link_message(
                    chat_id=chat_id,
                    amount_inr=agent_res.cart_total,
                    payment_link=agent_res.payment_link,
                    merchant_name=merchant.name if merchant else "Bangalore Store",
                )

        except Exception as exc:
            logger.error("Error processing Telegram update in poller: %s", exc, exc_info=True)
            await telegram_service.send_message(
                chat_id=chat_id,
                text="I encountered a temporary issue processing your request. Please try again!",
            )


async def run_telegram_polling():
    """Continuous long-polling loop pulling updates from Telegram Bot API."""
    token = settings.telegram_bot_token
    if not token or len(token.strip()) < 5:
        logger.info("Telegram Bot Token not configured. Polling worker inactive.")
        return

    api_url = f"https://api.telegram.org/bot{token}"
    offset = 0

    print("⚡ Autonomous Telegram Polling Daemon started for @utkarsh_merchantmind_bot", flush=True)
    logger.info("Autonomous Telegram Polling Daemon started for live bot.")
    async with httpx.AsyncClient(timeout=40.0) as client:
        while True:
            try:
                params = {"offset": offset, "timeout": 25, "allowed_updates": ["message", "callback_query"]}
                res = await client.get(f"{api_url}/getUpdates", params=params)
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = u["update_id"] + 1
                        asyncio.create_task(process_telegram_update(u))
                elif res.status_code == 409:
                    logger.warning("Telegram webhook conflict — waiting 5s...")
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(2)
            except asyncio.CancelledError:
                logger.info("Telegram polling daemon stopped.")
                break
            except Exception as exc:
                logger.warning("Transient error in Telegram polling: %s", exc)
                await asyncio.sleep(3)
