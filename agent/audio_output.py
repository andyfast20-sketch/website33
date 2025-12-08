"""Speaker playback utilities."""
from __future__ import annotations

import queue
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from .config import settings


class SpeakerStream:
    """Play audio frames immediately with stop support for barge-in."""

    def __init__(self):
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._stream: Optional[sd.OutputStream] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="SpeakerStream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._stream:
            self._stream.stop(ignore_errors=True)
            self._stream.close(ignore_errors=True)
        if self._thread:
            self._thread.join(timeout=1)

    def write(self, pcm: np.ndarray) -> None:
        """Enqueue PCM audio for playback."""
        if pcm.dtype != np.float32:
            pcm = pcm.astype(np.float32)
        self._queue.put(pcm)

    def clear(self) -> None:
        """Immediately drop queued audio for barge-in."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _run(self) -> None:
        try:
            def callback(outdata, frames, time, status):
                if status:
                    print(f"Speaker status: {status}")
                if self._stop_event.is_set():
                    raise sd.CallbackStop()
                try:
                    data = self._queue.get_nowait()
                except queue.Empty:
                    data = np.zeros(frames, dtype=np.float32)
                if len(data) < frames:
                    padded = np.zeros(frames, dtype=np.float32)
                    padded[: len(data)] = data
                    data = padded
                outdata[:, 0] = data[:frames]

            with sd.OutputStream(
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
            print(f"SpeakerStream error: {exc}")


class NullSpeakerStream(SpeakerStream):
    """A silent speaker for environments without audio devices."""

    def start(self) -> None:  # pragma: no cover
        self._stop_event.clear()

    def _run(self) -> None:  # pragma: no cover
        return
