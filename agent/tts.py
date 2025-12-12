"""Text-to-speech using OpenAI TTS API."""
from __future__ import annotations

import asyncio
from typing import AsyncIterable

import aiohttp
import sounddevice as sd
import numpy as np

from .config import settings
from .audio_output import SpeakerStream


async def _speak_openai(text: str, stop_event: asyncio.Event) -> None:
    """Use OpenAI TTS API to speak text."""
    print(f"[TTS] OpenAI speaking: {text[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "tts-1",  # tts-1 is faster, tts-1-hd is higher quality
        "input": text,
        "voice": "alloy",  # alloy is slightly faster than nova
        "response_format": "pcm",  # Raw PCM for direct playback
        "speed": 1.2,  # Faster speech
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/audio/speech",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"[TTS] OpenAI error: {error}")
                    await _speak_pyttsx3(text, stop_event)
                    return
                
                # Read audio data
                audio_data = await resp.read()
                
                if stop_event.is_set():
                    print("[TTS] Interrupted before playback")
                    return
                
                # Convert to numpy array (OpenAI PCM is 24kHz, 16-bit mono)
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Play audio
                print("[TTS] Playing audio...")
                sd.play(audio_np, samplerate=24000)
                sd.wait()
                print("[TTS] Finished")
                
    except Exception as e:
        print(f"[TTS] OpenAI error: {e}")
        # Fallback to pyttsx3
        await _speak_pyttsx3(text, stop_event)


async def _speak_pyttsx3(text: str, stop_event: asyncio.Event) -> None:
    """Fallback to pyttsx3."""
    import pyttsx3
    print("[TTS] Fallback to pyttsx3...")
    
    def speak():
        engine = pyttsx3.init()
        engine.setProperty('rate', 200)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    
    await asyncio.to_thread(speak)
    print("[TTS] Finished")


async def stream_tts(text_stream: AsyncIterable[str], speaker: SpeakerStream, *, stop_event: asyncio.Event) -> None:
    """Stream text and speak it."""
    full_text = ""
    
    async for chunk in text_stream:
        if stop_event.is_set():
            print("\n[TTS] Interrupted!")
            break
        full_text += chunk
        print(chunk, end="", flush=True)
    
    print()
    
    if stop_event.is_set() or not full_text.strip():
        return
    
    # Use OpenAI TTS
    if settings.openai_api_key:
        await _speak_openai(full_text, stop_event)
    else:
        await _speak_pyttsx3(full_text, stop_event)
