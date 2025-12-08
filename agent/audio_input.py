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
        """Begin streaming microphone audio on a background thread."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="MicrophoneStream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop microphone streaming immediately."""
        self._stop_event.set()
        if self._stream:
            self._stream.stop(ignore_errors=True)
            self._stream.close(ignore_errors=True)
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        try:
            frame_length = int(settings.sample_rate * settings.frame_duration_ms / 1000)

            def callback(indata, frames, time, status):
                if status:
                    print(f"Microphone status: {status}")
                if self._stop_event.is_set():
                    raise sd.CallbackStop()
                # Copy buffer to avoid referencing underlying memory
                pcm = np.copy(indata[:, 0]).astype(np.float32)
                asyncio.run_coroutine_threadsafe(self.queue.put(pcm), self.loop)

            with sd.InputStream(
                samplerate=settings.sample_rate,
                channels=settings.channels,
                blocksize=settings.block_size,
                dtype="float32",
                callback=callback,
            ) as stream:
                self._stream = stream
                while not self._stop_event.is_set():
                    sd.sleep(settings.frame_duration_ms)
        except Exception as exc:  # pragma: no cover - hardware dependent
            if self.on_error:
                self.on_error(exc)
            else:
                print(f"MicrophoneStream error: {exc}")


class MockMicrophoneStream(MicrophoneStream):
    """A mock microphone that generates silence for environments without audio hardware."""

    def _run(self) -> None:  # pragma: no cover - used only when hardware unavailable
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
