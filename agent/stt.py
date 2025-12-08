"""Streaming speech-to-text engines."""
from __future__ import annotations

import asyncio
import threading
from typing import Callable, Optional

import numpy as np

try:  # pragma: no cover - optional heavy dependency
    import whisper
except Exception:  # pragma: no cover
    whisper = None

try:  # pragma: no cover - optional network dependency
    from deepgram import Deepgram
except Exception:  # pragma: no cover
    Deepgram = None

from .config import settings


class STTStream:
    """Dispatch microphone frames to a streaming STT engine."""

    def __init__(
        self,
        on_transcript: Callable[[str, bool], None],
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.on_transcript = on_transcript
        self.loop = loop or asyncio.get_event_loop()
        self._frame_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    @property
    def queue(self) -> asyncio.Queue[np.ndarray]:
        return self._frame_queue

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="STTStream", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        if settings.use_mock_audio or (whisper is None and Deepgram is None):
            self._run_mock()
        elif whisper is not None:
            self._run_whisper()
        else:
            self._run_deepgram()

    def _run_mock(self) -> None:
        while not self._stop_event.is_set():
            try:
                text = input("[Mock STT] Type what you say: ")
                if text:
                    self.on_transcript(text, True)
            except KeyboardInterrupt:
                break

    def _run_whisper(self) -> None:  # pragma: no cover - hardware dependent
        model = whisper.load_model(settings.whisper_model)
        audio_buffer: list[np.ndarray] = []
        while not self._stop_event.is_set():
            future = asyncio.run_coroutine_threadsafe(self._frame_queue.get(), self.loop)
            pcm = future.result()
            if pcm is None:
                continue
            audio_buffer.append(pcm)
            if len(audio_buffer) < 10:
                continue
            audio_np = np.concatenate(audio_buffer)
            result = model.transcribe(audio_np, fp16=False, language="en", task="transcribe")
            text = result.get("text", "").strip()
            if text:
                self.on_transcript(text, True)
            audio_buffer = []

    def _run_deepgram(self) -> None:  # pragma: no cover - network dependent
        assert Deepgram is not None, "Deepgram SDK missing"
        dg_client = Deepgram(settings.deepgram_api_key)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._deepgram_session(dg_client))

    async def _deepgram_session(self, dg_client):  # pragma: no cover
        socket = await dg_client.transcription.live({
            "punctuate": True,
            "interim_results": True,
            "encoding": "linear16",
            "sample_rate": settings.sample_rate,
            "channels": settings.channels,
        })

        async def sender():
            while not self._stop_event.is_set():
                pcm = await self._frame_queue.get()
                if pcm is None:
                    continue
                await socket.send(pcm.tobytes())

        async def receiver():
            async for msg in socket:
                transcript = msg.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                is_final = msg.get("is_final", False)
                if transcript:
                    self.on_transcript(transcript, is_final)

        await asyncio.gather(sender(), receiver())
