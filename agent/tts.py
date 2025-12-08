"""Streaming text-to-speech utilities."""
from __future__ import annotations

import asyncio
from typing import Iterable

import numpy as np
import requests

from .config import settings
from .audio_output import SpeakerStream


async def stream_tts(text_stream: Iterable[str], speaker: SpeakerStream, *, stop_event: asyncio.Event) -> None:
    """Stream TTS output to the speaker, stopping immediately on interruption."""
    if settings.use_mock_tts or settings.elevenlabs_api_key is None:
        await _mock_tts(text_stream, speaker, stop_event=stop_event)
        return
    for text in text_stream:
        if stop_event.is_set():
            break
        audio = _elevenlabs_tts(text)
        if audio is None:
            continue
        await _play_chunks(audio, speaker, stop_event)


def _elevenlabs_tts(text: str) -> bytes | None:  # pragma: no cover - network dependent
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice}/stream"
    headers = {"xi-api-key": settings.elevenlabs_api_key, "Accept": "audio/mpeg"}
    payload = {"text": text, "model_id": "eleven_multilingual_v2"}
    resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
    if resp.status_code != 200:
        print(f"TTS error: {resp.text}")
        return None
    return resp.content


async def _play_chunks(audio_bytes: bytes, speaker: SpeakerStream, stop_event: asyncio.Event) -> None:
    # Placeholder: convert bytes to PCM. Real implementation would decode mp3/opus.
    pcm = np.frombuffer(audio_bytes, dtype=np.float32)
    speaker.write(pcm)
    await asyncio.sleep(len(pcm) / settings.sample_rate)


async def _mock_tts(text_stream: Iterable[str], speaker: SpeakerStream, *, stop_event: asyncio.Event) -> None:
    for chunk in text_stream:
        if stop_event.is_set():
            break
        duration = max(0.05, len(chunk) / 40.0)
        samples = int(duration * settings.sample_rate)
        tone = np.zeros(samples, dtype=np.float32)
        speaker.write(tone)
        await asyncio.sleep(duration)
