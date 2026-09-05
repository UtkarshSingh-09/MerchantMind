"""Telegram Bot API client service with resilient async delivery and inline Razorpay checkout."""

import asyncio
import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def clean_telegram_text(text: str) -> str:
    """Convert raw markdown tables and markdown asterisks into clean, elegant Telegram HTML."""
    if not text:
        return ""

    import re

    lines = text.split("\n")
    cleaned_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c).issubset({"-", " ", ":"}) for c in cells):
                in_table = True
                continue
            if not in_table and any(h.lower() in ["#", "store", "dish", "item", "name", "price"] for h in cells):
                in_table = True
                continue
            if in_table:
                meaningful = [c for c in cells if c and not set(c).issubset({"-", " "})]
                if len(meaningful) >= 4:
                    num = meaningful[0] if meaningful[0].isdigit() else ""
                    store = meaningful[1] if meaningful[0].isdigit() else meaningful[0]
                    dish = meaningful[2] if meaningful[0].isdigit() else meaningful[1]
                    price = meaningful[-1]
                    notes = meaningful[-2] if len(meaningful) >= 5 else ""

                    store = re.sub(r"\*\*(.+?)\*\*", r"\1", store)
                    dish = re.sub(r"\*\*(.+?)\*\*", r"\1", dish)
                    price = re.sub(r"\*\*(.+?)\*\*", r"\1", price)

                    num_prefix = f"{num}. " if num else "• "
                    cleaned_lines.append(f"\n{num_prefix}<b>{store}</b> — <b>{price}</b>")
                    notes_str = f" • <i>{notes}</i>" if notes and notes != price else ""
                    cleaned_lines.append(f"   <i>{dish}</i>{notes_str}")
                elif len(meaningful) >= 2:
                    p1 = re.sub(r"\*\*(.+?)\*\*", r"\1", meaningful[0])
                    p2 = re.sub(r"\*\*(.+?)\*\*", r"\1", meaningful[-1])
                    cleaned_lines.append(f"• <b>{p1}</b> — {p2}")
                continue
        else:
            in_table = False
            cleaned_lines.append(line)

    res = "\n".join(cleaned_lines)
    # Convert **bold** to <b>bold</b>
    res = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", res)
    # Convert *italic* to <i>italic</i>
    res = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", res)
    # Clean rogue pipes
    res = re.sub(r"^\|\s*\d+\s*\|\s*", "", res, flags=re.MULTILINE)
    res = re.sub(r"\s*\|\s*", " — ", res)
    return res.strip()


class TelegramService:
    """Async Telegram Bot API client supporting rich messages, inline keyboards, and Razorpay links."""

    def __init__(self):
        self.token = settings.telegram_bot_token

    @property
    def is_configured(self) -> bool:
        """Check if Telegram bot token is configured."""
        return bool(self.token and len(self.token.strip()) > 5)

    @property
    def api_url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    async def send_chat_action(self, chat_id: int | str, action: str = "typing") -> bool:
        """Broadcast status like 'typing' to the user's Telegram chat."""
        if not self.is_configured:
            return True

        url = f"{self.api_url}/sendChatAction"
        payload = {"chat_id": chat_id, "action": action}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=payload)
                return res.status_code == 200
        except Exception as exc:
            logger.debug("Failed to send chat action to %s: %s", chat_id, exc)
            return False

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        parse_mode: str | None = "HTML",
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Send a standard or styled message to a Telegram chat with automatic retry resilience."""
        text = clean_telegram_text(text)
        if len(text) > 4000:
            text = text[:3950] + "\n\n...(more options in store)"

        if not self.is_configured:
            logger.info("Telegram Bot not configured. Simulating send to chat %s: %s", chat_id, text[:80])
            return {"status": "simulated", "chat_id": chat_id, "text": text, "reply_markup": reply_markup}

        url = f"{self.api_url}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(max_retries):
                try:
                    res = await client.post(url, json=payload)
                    data = res.json()
                    if res.status_code >= 500:
                        logger.warning("Telegram 5xx error (%s) on attempt %d/%d", res.status_code, attempt + 1, max_retries)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5 * (2 ** attempt))
                            continue
                    elif res.status_code >= 400:
                        logger.error("Telegram API 4xx error (%s): %s", res.status_code, data)
                        # Retry without parse_mode and with HTML tags stripped
                        if "can't parse entities" in str(data) and parse_mode:
                            logger.info("Retrying message to %s after stripping HTML tags...", chat_id)
                            import re
                            payload.pop("parse_mode", None)
                            payload["text"] = re.sub(r"<[^>]+>", "", text)
                            res2 = await client.post(url, json=payload)
                            return res2.json()
                        return data

                    logger.info("Successfully dispatched Telegram message to chat %s", chat_id)
                    return data
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    logger.warning("Network issue sending to Telegram chat %s (attempt %d/%d): %s", chat_id, attempt + 1, max_retries, exc)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                    else:
                        return {"error": str(exc)}
                except Exception as exc:
                    logger.error("Fatal exception dispatching Telegram message: %s", exc)
                    return {"error": str(exc)}
            return {"error": "Max retries exceeded"}

    async def send_interactive_buttons(
        self,
        chat_id: int | str,
        text: str,
        buttons: list[dict[str, str]],
        parse_mode: str | None = "HTML",
    ) -> dict[str, Any]:
        """Send a message with inline keyboard buttons formatted comfortably for mobile."""
        keyboard_rows: list[list[dict[str, str]]] = []
        current_row: list[dict[str, str]] = []

        for btn in buttons:
            btn_obj = {"text": btn["text"]}
            if "url" in btn:
                btn_obj["url"] = btn["url"]
            elif "callback_data" in btn:
                btn_obj["callback_data"] = btn["callback_data"]
            else:
                btn_obj["callback_data"] = btn["text"]

            # If button text is long (>18 chars), give it a dedicated full-width row
            if len(btn["text"]) > 18:
                if current_row:
                    keyboard_rows.append(current_row)
                    current_row = []
                keyboard_rows.append([btn_obj])
            else:
                current_row.append(btn_obj)
                if len(current_row) == 2:
                    keyboard_rows.append(current_row)
                    current_row = []

        if current_row:
            keyboard_rows.append(current_row)

        reply_markup = {"inline_keyboard": keyboard_rows}
        return await self.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    async def send_payment_link_message(
        self,
        chat_id: int | str,
        amount_inr: float,
        payment_link: str,
        merchant_name: str = "MerchantMind Store",
    ) -> dict[str, Any]:
        """Send a formatted Razorpay payment message featuring a high-contrast inline checkout button."""
        text = (
            f"🛍️ <b>Order Ready for {merchant_name}</b>\n\n"
            f"Your order total is <b>₹{amount_inr:.2f}</b>.\n\n"
            f"Click the button below to pay securely via <b>Razorpay</b> (UPI, Cards, NetBanking):\n"
            f"<code>{payment_link}</code>\n\n"
            f"<i>Your order will be instantly confirmed and prepped upon payment!</i>"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": f"💳 Pay ₹{amount_inr:.0f} via Razorpay",
                        "url": payment_link,
                    }
                ],
                [
                    {
                        "text": "🛍️ Add More Items",
                        "callback_data": "continue_shopping",
                    }
                ],
            ]
        }

        return await self.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    async def set_webhook(self, webhook_url: str, secret_token: str | None = None) -> dict[str, Any]:
        """Configure Telegram webhook endpoint."""
        if not self.is_configured:
            return {"status": "simulated", "webhook_url": webhook_url}

        url = f"{self.api_url}/setWebhook"
        payload: dict[str, Any] = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
        }
        if secret_token:
            payload["secret_token"] = secret_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=payload)
            return res.json()


telegram_service = TelegramService()
