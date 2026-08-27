"""Tests for WhatsApp Meta Cloud API webhooks and conversational flow."""

import uuid
import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.mark.asyncio
async def test_whatsapp_webhook_verification_challenge(client: AsyncClient):
    """GET /api/webhooks/whatsapp — Meta challenge verification."""
    verify_token = settings.whatsapp_verify_token or "merchantmind_secret_verify_token_2026"
    challenge_str = "challenge_123456789"

    # Valid token
    res = await client.get(
        "/api/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": verify_token,
            "hub.challenge": challenge_str,
        },
    )
    assert res.status_code == 200
    assert res.text == challenge_str

    # Invalid token -> 403
    bad_res = await client.get(
        "/api/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": challenge_str,
        },
    )
    assert bad_res.status_code == 403


@pytest.mark.asyncio
async def test_whatsapp_webhook_incoming_message(client: AsyncClient):
    """POST /api/webhooks/whatsapp — incoming customer message triggers CheckoutAgent."""
    # Ensure at least one active merchant exists
    unique_email = f"wa_merchant_{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/api/merchants/",
        json={"name": "WhatsApp Test Bakery", "email": unique_email},
    )

    sample_meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550255555",
                                "phone_number_id": "1073619675834411",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Utkarsh Singh"},
                                    "wa_id": "919876543210",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": f"wamid.{uuid.uuid4().hex}",
                                    "timestamp": "1724580000",
                                    "text": {"body": "Hi, do you have fresh chocolate cake?"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    res = await client.post("/api/webhooks/whatsapp", json=sample_meta_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
