"""Microphone streaming utilities."""
from __future__ import annotations

import asyncio
import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from .config import settings


class MicrophoneStream:
    """Continuously capture audio from the default microphone into an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        self.queue = queue
        self.loop = loop or asyncio.get_event_loop()
        self.on_error = on_error
        self._stream: Optional[sd.InputStream] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="MicrophoneStream", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._stream:
            self._stream.stop()
            self._stream.close()
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        try:
            frame_length = int(settings.sample_rate * settings.frame_duration_ms / 1000)
            frame_count = 0

            def callback(indata, frames, time, status):
                nonlocal frame_count
                if status:
                    print(f"Microphone status: {status}")
                if self._stop_event.is_set():
                    raise sd.CallbackStop()

                pcm = np.copy(indata[:, 0]).astype(np.float32)
                self.queue.put(pcm)  # Thread-safe queue
                
                frame_count += 1
                if frame_count % 100 == 0:
                    print(f"[MIC] Captured {frame_count} frames, last max: {np.max(np.abs(pcm)):.4f}")

            # Use WASAPI device for better audio quality
            mic_device = 19  # Jabra EVOLVE 20 via WASAPI
            print(f"[MIC] Opening microphone (device {mic_device})...")
            with sd.InputStream(
                device=mic_device,
                samplerate=settings.sample_rate,
                channels=settings.channels,
                blocksize=settings.block_size,
                dtype="float32",
                callback=callback,
            ) as stream:
                self._stream = stream
                print("[MIC] Microphone opened successfully!")
                while not self._stop_event.is_set():
                    sd.sleep(settings.frame_duration_ms)

        except Exception as exc:
            if self.on_error:
                self.on_error(exc)
            else:
                print(f"MicrophoneStream error: {exc}")


class MockMicrophoneStream(MicrophoneStream):
    """Mock mic that generates silence (for testing environments)."""

    def _run(self) -> None:
        frame_length = int(settings.sample_rate * settings.frame_duration_ms / 1000)
        silence = np.zeros(frame_length, dtype=np.float32)
        try:
            while not self._stop_event.is_set():
                asyncio.run_coroutine_threadsafe(self.queue.put(silence.copy()), self.loop)
                sd.sleep(settings.frame_duration_ms)
        except Exception as exc:
            if self.on_error:
                self.on_error(exc)
            else:
                print(f"MockMicrophoneStream error: {exc}")
