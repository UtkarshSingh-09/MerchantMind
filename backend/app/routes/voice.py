"""Voice AI service routes — Deepgram Aura TTS integration with resilient fallback."""

import logging
from typing import Any
import httpx
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice AI"])

# Persistent HTTP/2 connection pool to avoid TCP/TLS handshake latency on every voice turn
_http_pool: httpx.AsyncClient | None = None


def get_deepgram_client() -> httpx.AsyncClient:
    global _http_pool
    if _http_pool is None or _http_pool.is_closed:
        _http_pool = httpx.AsyncClient(
            timeout=12.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0),
        )
    return _http_pool


class VoiceSpeakRequest(BaseModel):
    text: str
    model: str | None = None


@router.get("/status")
async def get_voice_status() -> dict[str, Any]:
    """Check if Deepgram Voice AI service is configured and ready."""
    is_enabled = bool(settings.deepgram_api_key and len(settings.deepgram_api_key.strip()) > 5)
    return {
        "provider": "deepgram_flux" if is_enabled else "browser_speech_synthesis",
        "deepgram_enabled": is_enabled,
        "default_model": settings.deepgram_voice_model,
        "fallback_available": True,
    }


@router.post("/speak")
async def speak_text_deepgram(payload: VoiceSpeakRequest):
    """Convert text to ultra-realistic studio speech audio using Deepgram Voice API.

    Returns fast low-latency audio/mpeg stream directly to client.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty")

    if not settings.deepgram_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deepgram API key not configured. Fallback to client speech synthesis.",
        )

    voice_model = payload.model or settings.deepgram_voice_model or "flux-meena-en"
    endpoint_version = "v2" if voice_model.startswith("flux-") else "v1"
    deepgram_url = f"https://api.deepgram.com/{endpoint_version}/speak?model={voice_model}"

    headers = {
        "Authorization": f"Token {settings.deepgram_api_key.strip()}",
        "Content-Type": "application/json",
    }

    client = get_deepgram_client()

    try:
        req = client.build_request("POST", deepgram_url, headers=headers, json={"text": payload.text.strip()})
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            err_bytes = await resp.aread()
            logger.warning("Deepgram API returned %d: %s", resp.status_code, err_bytes.decode(errors="ignore"))
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Deepgram TTS failed: {err_bytes.decode(errors='ignore')}",
            )

        return StreamingResponse(
            resp.aiter_bytes(),
            media_type="audio/mpeg",
            headers={
                "Content-Type": "audio/mpeg",
                "Content-Disposition": "inline; filename=speech.mp3",
                "Cache-Control": "public, max-age=3600",
            },
        )
    except httpx.RequestError as exc:
        logger.error("Deepgram connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Deepgram network error: {str(exc)}",
        )
