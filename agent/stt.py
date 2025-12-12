"""STT using OpenAI Whisper API - accurate and fast."""
from __future__ import annotations

import asyncio
import threading
import io
from typing import Callable, Optional

import numpy as np
import aiohttp
from scipy.io import wavfile
from scipy import signal

from .config import settings


class STTStream:
    def __init__(self, on_transcript: Callable[[str, bool], None], *, mic_queue=None):
        self.on_transcript = on_transcript
        self.mic_queue = mic_queue
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.paused = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_sync, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_sync(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        print("[STT] Using OpenAI Whisper API (accurate)")
        
        speech_threshold = 0.015  # Threshold for detecting speech
        silence_frames = 0
        max_silence = 45  # Wait ~1.4 seconds of silence before processing
        min_audio_frames = 50  # Minimum frames before considering it speech
        
        audio_buffer = []
        speech_started = False
        consecutive_speech = 0  # Need multiple speech frames to start
        
        while not self._stop_event.is_set():
            if self.paused:
                while not self.mic_queue.empty():
                    try: self.mic_queue.get_nowait()
                    except: break
                audio_buffer = []
                speech_started = False
                silence_frames = 0
                consecutive_speech = 0
                await asyncio.sleep(0.05)
                continue
            
            if self.mic_queue.empty():
                await asyncio.sleep(0.01)
                continue
            
            try:
                frame = self.mic_queue.get_nowait()
            except:
                continue
            
            if frame is None:
                continue
            
            max_amp = np.max(np.abs(frame))
            
            if max_amp > speech_threshold:
                consecutive_speech += 1
                silence_frames = 0
                audio_buffer.append(frame)
                
                # Only start speech after several consecutive speech frames
                if consecutive_speech >= 3:
                    speech_started = True
            else:
                consecutive_speech = 0
                if speech_started:
                    audio_buffer.append(frame)
                    silence_frames += 1
                    
                    # Process after silence
                    if silence_frames > max_silence and len(audio_buffer) > min_audio_frames:
                        await self._transcribe_and_callback(audio_buffer)
                        audio_buffer = []
                        speech_started = False
                        silence_frames = 0
            
            # Safety: max 10 seconds
            if len(audio_buffer) > 350:
                await self._transcribe_and_callback(audio_buffer)
                audio_buffer = []
                speech_started = False
                silence_frames = 0
                consecutive_speech = 0

    async def _transcribe_and_callback(self, chunks):
        if not chunks:
            return
        
        audio = np.concatenate(chunks)
        
        # Resample from 44100Hz to 16000Hz for Whisper
        num_samples_out = int(len(audio) * settings.whisper_rate / settings.sample_rate)
        audio_resampled = signal.resample(audio, num_samples_out)
        
        max_val = np.max(np.abs(audio_resampled))
        print(f"[STT] Sending {len(audio_resampled)/settings.whisper_rate:.1f}s audio (max amplitude: {max_val:.4f})")
        
        # Light boost if quiet
        if max_val > 0.001 and max_val < 0.3:
            boost_factor = min(5, 0.5 / max_val)
            audio_resampled = audio_resampled * boost_factor
            audio_resampled = np.clip(audio_resampled, -1.0, 1.0)
        
        # Convert to WAV at 16kHz for Whisper
        audio_int16 = (audio_resampled * 32767).astype(np.int16)
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, settings.whisper_rate, audio_int16)
        wav_buffer.seek(0)
        
        # Call OpenAI API
        try:
            headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            
            data = aiohttp.FormData()
            data.add_field('file', wav_buffer, filename='audio.wav', content_type='audio/wav')
            data.add_field('model', 'whisper-1')
            data.add_field('language', 'en')
            data.add_field('response_format', 'text')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        text = (await resp.text()).strip()
                        if text and len(text) > 1:
                            print(f"[STT] You said: {text}")
                            self.on_transcript(text, True)
                    else:
                        print(f"[STT] Error: {resp.status}")
        except Exception as e:
            print(f"[STT] Error: {e}")
