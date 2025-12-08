"""Main loop orchestrating microphone, STT, LLM, and TTS."""
from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Optional

import numpy as np

from .audio_input import MicrophoneStream, MockMicrophoneStream
from .audio_output import NullSpeakerStream, SpeakerStream
from .barge_in import BargeInDetector
from .config import settings
from .llm import llm_stream
from .states import STATE_LISTENING, STATE_SPEAKING, STATE_THINKING
from .stt import STTStream
from .tts import stream_tts


class AgentApp:
    """Coordinates full-duplex audio conversation."""

    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.mic_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self.state = STATE_LISTENING

        self.speaker: SpeakerStream = NullSpeakerStream() if settings.use_mock_audio else SpeakerStream()
        mic_cls = MockMicrophoneStream if settings.use_mock_audio else MicrophoneStream
        self.microphone = mic_cls(self.mic_queue, loop=self.loop)

        self.stt = STTStream(self._on_transcript, loop=self.loop)
        self.barge_in = BargeInDetector(self.mic_queue)
        self.stop_llm_event = asyncio.Event()
        self.stop_tts_event = asyncio.Event()
        self.barge_in.attach_stop_event(self.stop_llm_event)
        self.barge_in.attach_stop_event(self.stop_tts_event)

        self._stack = AsyncExitStack()

    def _on_transcript(self, text: str, is_final: bool) -> None:
        if not text:
            return
        print(f"[STT] {'FINAL' if is_final else 'PARTIAL'}: {text}")
        if not is_final:
            return
        asyncio.run_coroutine_threadsafe(self._handle_user_text(text), self.loop)

    async def _handle_user_text(self, text: str) -> None:
        self._set_state(STATE_THINKING)
        self.stop_llm_event.clear()
        self.stop_tts_event.clear()
        self.speaker.clear()

        async def token_generator():
            queue: asyncio.Queue[str] = asyncio.Queue()

            def on_token(token: str) -> None:
                queue.put_nowait(token)

            llm_task = asyncio.create_task(
                llm_stream(text, on_token, stop_event=self.stop_llm_event)
            )
            try:
                while True:
                    token = await queue.get()
                    yield token
            finally:
                self.stop_tts_event.set()
                await llm_task

        self._set_state(STATE_SPEAKING)
        await stream_tts(token_generator(), self.speaker, stop_event=self.stop_tts_event)
        self._set_state(STATE_LISTENING)

    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        self.barge_in.set_state(new_state)
        print(f"[STATE] -> {new_state}")

    async def _start_background(self) -> None:
        self.speaker.start()
        self.microphone.start()
        self.stt.start()
        asyncio.create_task(self.barge_in.monitor())

    async def run(self, runtime: Optional[float] = None) -> None:
        """Run the agent. Pass runtime to auto-stop after N seconds."""
        await self._start_background()
        print("Agent is running. Speak into your mic.")
        try:
            if runtime:
                await asyncio.sleep(runtime)
            else:
                while True:
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stopping agent...")
        finally:
            self.stop()

    def stop(self) -> None:
        self.stop_llm_event.set()
        self.stop_tts_event.set()
        self.stt.stop()
        self.microphone.stop()
        self.speaker.stop()


def main():  # pragma: no cover - entrypoint
    app = AgentApp()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
