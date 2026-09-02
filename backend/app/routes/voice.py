"""Voice AI service routes — Deepgram Aura TTS integration with resilient fallback."""

import logging
from typing import Any
import httpx
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice AI"])


class VoiceSpeakRequest(BaseModel):
    text: str
    model: str | None = None


@router.get("/status")
async def get_voice_status() -> dict[str, Any]:
    """Check if Deepgram Aura Voice AI service is configured and ready."""
    is_enabled = bool(settings.deepgram_api_key and len(settings.deepgram_api_key.strip()) > 5)
    return {
        "provider": "deepgram_aura" if is_enabled else "browser_speech_synthesis",
        "deepgram_enabled": is_enabled,
        "default_model": settings.deepgram_voice_model,
        "fallback_available": True,
    }


@router.post("/speak")
async def speak_text_deepgram(payload: VoiceSpeakRequest):
    """Convert text to ultra-realistic studio speech audio using Deepgram Aura TTS API.

    Returns audio/mpeg stream directly to client.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty")

    if not settings.deepgram_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Deepgram API key not configured. Fallback to client speech synthesis.",
        )

    voice_model = payload.model or settings.deepgram_voice_model or "aura-asteria-en"
    deepgram_url = f"https://api.deepgram.com/v1/speak?model={voice_model}"

    headers = {
        "Authorization": f"Token {settings.deepgram_api_key.strip()}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                deepgram_url,
                headers=headers,
                json={"text": payload.text.strip()},
            )

            if resp.status_code != 200:
                logger.warning("Deepgram API returned %d: %s", resp.status_code, resp.text)
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Deepgram TTS failed: {resp.text}",
                )

            return Response(
                content=resp.content,
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
