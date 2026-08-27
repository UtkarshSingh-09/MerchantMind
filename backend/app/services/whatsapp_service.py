"""Meta WhatsApp Cloud API (v21.0) client wrapper with retry backoff and failure resilience."""

import asyncio
import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Meta WhatsApp Cloud API client service with automatic retry on transient failures."""

    BASE_URL = "https://graph.facebook.com/v21.0"

    def __init__(self):
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id

    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp credentials are provided."""
        return bool(self.access_token and self.phone_number_id)

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        to: str,
        text: str,
        preview_url: bool = True,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Send a standard text message to a WhatsApp number with retry resilience."""
        if not self.is_configured:
            logger.warning("WhatsApp API is not configured. Simulating send to %s: %s", to, text[:60])
            return {"status": "simulated", "to": to, "text": text}

        clean_to = "".join(filter(str.isdigit, to))
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            for attempt in range(max_retries):
                try:
                    res = await client.post(url, json=payload, headers=self._get_headers())
                    data = res.json()
                    if res.status_code >= 500:
                        logger.warning("Meta API 5xx error (%s) on attempt %d/%d", res.status_code, attempt + 1, max_retries)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5 * (2 ** attempt))
                            continue
                    elif res.status_code >= 400:
                        logger.error("Meta WhatsApp API 4xx error (%s): %s", res.status_code, data)
                        return data

                    logger.info("Successfully sent WhatsApp text message to %s", clean_to)
                    return data
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    logger.warning("Network error sending WhatsApp to %s (attempt %d/%d): %s", clean_to, attempt + 1, max_retries, exc)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                    else:
                        return {"error": str(exc)}
                except Exception as exc:
                    logger.error("Fatal error sending WhatsApp text: %s", exc)
                    return {"error": str(exc)}
            return {"error": "Max retries exceeded"}

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Send an interactive button message (max 3 buttons)."""
        if not self.is_configured:
            logger.warning("WhatsApp API not configured. Simulating buttons to %s: %s", to, buttons)
            return {"status": "simulated", "to": to, "body": body_text, "buttons": buttons}

        clean_to = "".join(filter(str.isdigit, to))
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"

        formatted_buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": b.get("id", f"btn_{i}")[:256],
                    "title": b.get("title", f"Option {i+1}")[:20],
                },
            }
            for i, b in enumerate(buttons[:3])
        ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text[:1024]},
                "action": {"buttons": formatted_buttons},
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                res = await client.post(url, json=payload, headers=self._get_headers())
                return res.json()
            except Exception as exc:
                logger.error("Failed to send WhatsApp buttons: %s", exc)
                return {"error": str(exc)}

    async def send_payment_link_message(
        self,
        to: str,
        amount_inr: float,
        payment_link: str,
        merchant_name: str = "MerchantMind Store",
    ) -> dict[str, Any]:
        """Send a dedicated Razorpay payment link message with formatted CTA."""
        text = (
            f"🛍️ *Order Payment for {merchant_name}*\n\n"
            f"Your order total is *₹{amount_inr:.2f}*.\n\n"
            f"👉 Click here to pay securely with Razorpay:\n{payment_link}\n\n"
            f"_Once paid, your order will immediately be confirmed!_"
        )
        return await self.send_text_message(to=to, text=text, preview_url=True)

    async def mark_as_read(self, message_id: str) -> None:
        """Mark an incoming customer message as read."""
        if not self.is_configured or not message_id:
            return

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                await client.post(url, json=payload, headers=self._get_headers())
            except Exception as exc:
                logger.debug("Failed to mark message %s as read: %s", message_id, exc)


whatsapp_service = WhatsAppService()
