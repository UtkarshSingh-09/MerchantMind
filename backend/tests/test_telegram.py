"""Tests for Telegram Bot API webhooks, session handling, and conversational commerce."""

import uuid
import pytest
from httpx import AsyncClient

from app.config import settings
from app.services.telegram_service import telegram_service


@pytest.mark.asyncio
async def test_telegram_webhook_start_command(client: AsyncClient):
    """POST /api/webhooks/telegram — /start command delivers welcome message and quick action buttons."""
    payload = {
        "update_id": 990001,
        "message": {
            "message_id": 101,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Utkarsh",
                "last_name": "Singh",
                "username": "utkarsh_tg",
            },
            "chat": {
                "id": 123456789,
                "first_name": "Utkarsh",
                "type": "private",
            },
            "date": 1725350000,
            "text": "/start",
        },
    }

    res = await client.post("/api/webhooks/telegram", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "started"}


@pytest.mark.asyncio
async def test_telegram_webhook_incoming_message(client: AsyncClient):
    """POST /api/webhooks/telegram — incoming customer shopping query triggers Agent pipeline."""
    # Ensure at least one active merchant exists
    unique_email = f"tg_merchant_{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/merchants/",
        json={"name": "Telegram Test Bakery", "email": unique_email},
    )

    payload = {
        "update_id": 990002,
        "message": {
            "message_id": 102,
            "from": {
                "id": 987654321,
                "is_bot": False,
                "first_name": "Ananya",
                "last_name": "Sharma",
                "username": "ananya_s",
            },
            "chat": {
                "id": 987654321,
                "first_name": "Ananya",
                "type": "private",
            },
            "date": 1725350005,
            "text": "want to buy ghee masala dosa under 200",
        },
    }

    res = await client.post("/api/webhooks/telegram", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_telegram_webhook_button_callback(client: AsyncClient):
    """POST /api/webhooks/telegram — user clicking an inline keyboard button triggers callback_query."""
    payload = {
        "update_id": 990003,
        "callback_query": {
            "id": "cb_query_9999",
            "from": {
                "id": 987654321,
                "first_name": "Ananya",
                "username": "ananya_s",
            },
            "message": {
                "message_id": 102,
                "chat": {"id": 987654321},
            },
            "data": "Add 1 Ghee Roast Masala Dosa to my cart",
        },
    }

    res = await client.post("/api/webhooks/telegram", json=payload)
    assert res.status_code == 200
    assert res.json() == {"status": "success"}


@pytest.mark.asyncio
async def test_telegram_service_simulation():
    """Verify TelegramService gracefully simulates messaging when no live bot token is set."""
    orig_token = telegram_service.token
    telegram_service.token = ""
    try:
        # Test send_message
        res_msg = await telegram_service.send_message(
            chat_id=123456789,
            text="Hello from simulated Telegram!",
        )
        assert res_msg.get("status") == "simulated"
        assert res_msg.get("chat_id") == 123456789

        # Test send_interactive_buttons
        res_btn = await telegram_service.send_interactive_buttons(
            chat_id=123456789,
            text="Choose an option:",
            buttons=[{"text": "Option 1", "callback_data": "opt1"}],
        )
        assert res_btn.get("status") == "simulated"

        # Test send_payment_link_message
        res_pay = await telegram_service.send_payment_link_message(
            chat_id=123456789,
            amount_inr=250.0,
            payment_link="https://rzp.io/i/testlink",
            merchant_name="Bangalore Sweets",
        )
        assert res_pay.get("status") == "simulated"
    finally:
        telegram_service.token = orig_token


@pytest.mark.asyncio
async def test_telegram_secret_token_verification(client: AsyncClient):
    """POST /api/webhooks/telegram — verifies 403 when secret token header doesn't match."""
    original_secret = settings.telegram_webhook_secret
    settings.telegram_webhook_secret = "super_secret_tg_token_123"

    try:
        payload = {
            "update_id": 990004,
            "message": {
                "chat": {"id": 123456},
                "text": "test",
            },
        }

        # Request without header or with wrong header
        res_bad = await client.post(
            "/api/webhooks/telegram",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
        )
        assert res_bad.status_code == 403

        # Request with correct header
        res_good = await client.post(
            "/api/webhooks/telegram",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_tg_token_123"},
        )
        assert res_good.status_code == 200
    finally:
        settings.telegram_webhook_secret = original_secret
