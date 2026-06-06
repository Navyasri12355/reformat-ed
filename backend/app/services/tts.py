"""Text-to-speech with per-neurodivergent-profile voice modulation.

Each output format gets its own voice character, chosen for the learner:

* ``dyslexia_audio``  → slow, clear, evenly paced — easiest to decode by ear.
* ``adhd_gamified``   → brighter, a little faster and higher — energetic, holds
                        attention.
* ``asd_structured``  → calm, steady, minimal emotional swing — predictable.
* ``blended``         → a balanced middle ground.

Primary engine is **Coqui TTS** (``pip install TTS``), synthesised server-side
and modulated with librosa when available. If Coqui is not installed the API
reports ``engine="browser"`` and the frontend speaks with the Web Speech API
using the *same* rate/pitch numbers — so the per-profile modulation is identical
either way.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from app.config import settings

# Coqui's LJSpeech model speaks at roughly this pace; used to derive a stretch
# factor from a target words-per-minute.
_COQUI_BASE_WPM = 150.0


@dataclass(frozen=True)
class VoiceProfile:
    format: str
    style: str
    rate_wpm: int  # target speaking pace
    browser_rate: float  # Web Speech API rate multiplier (1.0 = normal)
    browser_pitch: float  # Web Speech API pitch multiplier (1.0 = normal)
    pitch_semitones: float = 0.0  # Coqui pitch shift
    emphasis_pauses: bool = False  # insert short pauses at sentence ends

    @property
    def coqui_speed(self) -> float:
        return round(self.rate_wpm / _COQUI_BASE_WPM, 3)


VOICE_PROFILES: dict[str, VoiceProfile] = {
    "dyslexia_audio": VoiceProfile(
        format="dyslexia_audio",
        style="Slow, clear and evenly paced, with short pauses between sentences.",
        rate_wpm=130, browser_rate=0.80, browser_pitch=1.0, pitch_semitones=0.0,
        emphasis_pauses=True,
    ),
    "adhd_gamified": VoiceProfile(
        format="adhd_gamified",
        style="Bright, energetic and a little faster, with lively intonation.",
        rate_wpm=185, browser_rate=1.08, browser_pitch=1.12, pitch_semitones=1.5,
    ),
    "asd_structured": VoiceProfile(
        format="asd_structured",
        style="Calm, steady and predictable, with minimal emotional variation.",
        rate_wpm=150, browser_rate=0.92, browser_pitch=0.98, pitch_semitones=-1.0,
        emphasis_pauses=True,
    ),
    "blended": VoiceProfile(
        format="blended",
        style="Balanced pace with gentle, clear structure.",
        rate_wpm=160, browser_rate=0.95, browser_pitch=1.04, pitch_semitones=0.5,
    ),
}

DEFAULT_PROFILE = VOICE_PROFILES["asd_structured"]


def get_voice_profile(output_format: str) -> VoiceProfile:
    return VOICE_PROFILES.get(output_format, DEFAULT_PROFILE)


# --------------------------------------------------------------------------- #
# Engine availability + synthesis
# --------------------------------------------------------------------------- #
_engine_cache: dict[str, object] = {}


def _apply_compat_shims() -> None:
    """The only coqui-tts builds that run on Python 3.13 import a couple of
    helpers that newer `transformers` versions renamed/removed. Re-provide them
    so the TTS package imports cleanly."""
    try:
        import torch
        import transformers.pytorch_utils as _tpu

        if not hasattr(_tpu, "isin_mps_friendly"):
            _tpu.isin_mps_friendly = lambda elements, test_elements: torch.isin(elements, test_elements)
    except Exception:
        pass


def coqui_available() -> bool:
    """Cheap check that the Coqui package is installed — does NOT import it (which
    would load PyTorch and block for tens of seconds). The heavy import happens
    only when audio is actually synthesised; if that fails, the client falls back
    to the browser voice."""
    import importlib.util

    return importlib.util.find_spec("TTS") is not None


def profile_payload(output_format: str) -> dict:
    p = get_voice_profile(output_format)
    return {
        "format": p.format,
        "engine": "coqui" if coqui_available() else "browser",
        "style": p.style,
        "rate_wpm": p.rate_wpm,
        "browser_rate": p.browser_rate,
        "browser_pitch": p.browser_pitch,
        "coqui_speed": p.coqui_speed,
        "pitch_semitones": p.pitch_semitones,
    }


def _get_coqui():
    if "tts" not in _engine_cache:
        _apply_compat_shims()
        from TTS.api import TTS as CoquiTTS  # lazy, heavy import

        model = getattr(settings, "coqui_model", None) or "tts_models/en/ljspeech/tacotron2-DDC"
        _engine_cache["tts"] = CoquiTTS(model_name=model, progress_bar=False)
    return _engine_cache["tts"]


def synthesize_wav(text: str, output_format: str) -> bytes:
    """Synthesize speech with Coqui and apply per-profile modulation.

    Raises RuntimeError if Coqui is not installed (caller should fall back to
    the browser voice using :func:`profile_payload`).
    """
    if not coqui_available():
        raise RuntimeError("Coqui TTS is not installed (pip install TTS)")

    profile = get_voice_profile(output_format)
    tts = _get_coqui()

    import numpy as np

    wav = np.asarray(tts.tts(text=text), dtype=np.float32)
    sample_rate = int(getattr(tts.synthesizer, "output_sample_rate", 22050))

    wav = _modulate(wav, sample_rate, profile)
    return _to_wav_bytes(wav, sample_rate)


def _modulate(wav, sample_rate: int, profile: VoiceProfile):
    """Apply speed + pitch modulation with librosa if present; else return as-is."""
    try:
        import librosa
        import numpy as np
    except Exception:
        return wav

    out = wav
    speed = profile.coqui_speed
    if abs(speed - 1.0) > 0.02:
        out = librosa.effects.time_stretch(out, rate=speed)
    if abs(profile.pitch_semitones) > 0.05:
        out = librosa.effects.pitch_shift(out, sr=sample_rate, n_steps=profile.pitch_semitones)
    return np.ascontiguousarray(out)


def _to_wav_bytes(wav, sample_rate: int) -> bytes:
    import wave

    import numpy as np

    clipped = np.clip(wav, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()
