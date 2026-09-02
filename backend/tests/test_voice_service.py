"""Automated Test Suite for Deepgram Aura Voice AI & Resilient Fallback."""

import pytest
from httpx import AsyncClient, Response
from unittest.mock import patch, AsyncMock

from app.config import settings


@pytest.mark.asyncio
async def test_voice_status_endpoint(client: AsyncClient):
    """GET /api/voice/status returns provider and fallback readiness."""
    resp = await client.get("/api/voice/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "deepgram_enabled" in data
    assert data["fallback_available"] is True


@pytest.mark.asyncio
async def test_voice_speak_empty_text_rejection(client: AsyncClient):
    """POST /api/voice/speak rejects empty text with 400."""
    resp = await client.post("/api/voice/speak", json={"text": "   "})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_voice_speak_without_key_triggers_fallback_error(client: AsyncClient):
    """POST /api/voice/speak returns 503 service unavailable when no key is set."""
    with patch.object(settings, "deepgram_api_key", ""):
        resp = await client.post("/api/voice/speak", json={"text": "Hello world"})
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_voice_speak_mocked_deepgram_success(client: AsyncClient):
    """POST /api/voice/speak streams audio/mpeg bytes when Deepgram responds with 200."""
    mock_audio_bytes = b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03DeepgramAura"

    class MockStreamingResponse:
        status_code = 200

        async def aiter_bytes(self):
            yield mock_audio_bytes

    mock_client = AsyncMock()
    mock_client.build_request.return_value = "mock_request"
    mock_client.send.return_value = MockStreamingResponse()

    with patch.object(settings, "deepgram_api_key", "mock_dg_key_12345"):
        with patch("app.routes.voice.get_deepgram_client", return_value=mock_client):
            resp = await client.post(
                "/api/voice/speak",
                json={"text": "Your Veg Manchurian order is confirmed!"},
            )
            assert resp.status_code == 200
            assert "audio/mpeg" in resp.headers.get("content-type", "")
            assert resp.content == mock_audio_bytes
