"""Text-to-speech endpoints.

* ``GET /tts/profile?format=…`` → the voice-modulation parameters for a format
  (always available; used by the browser fallback too).
* ``POST /tts/audio`` → server-synthesised WAV via Coqui (503 if not installed,
  signalling the client to use the browser voice).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from app.auth import get_current_user
from app.models import User
from app.services import tts

router = APIRouter(prefix="/tts", tags=["tts"])


@router.get("/profile")
def voice_profile(format: str = Query("asd_structured")) -> dict:
    return tts.profile_payload(format)


class SynthesizeRequest(BaseModel):
    text: str
    format: str = "asd_structured"


@router.post("/audio")
def synthesize(body: SynthesizeRequest, _user: User = Depends(get_current_user)) -> Response:
    if not tts.coqui_available():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Coqui TTS not installed; use the browser voice via /tts/profile",
        )
    text = body.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "text is required")
    audio = tts.synthesize_wav(text[:2000], body.format)
    return Response(content=audio, media_type="audio/wav")
