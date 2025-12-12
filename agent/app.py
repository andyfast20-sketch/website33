"""Main loop orchestrating microphone, STT, LLM, and TTS."""
from __future__ import annotations

import asyncio
import queue
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
        # Make the current AgentApp globally accessible
        AgentApp.instance = self

        self.loop = asyncio.get_event_loop()
        self.mic_queue = queue.Queue()  # Thread-safe queue
        self.state = STATE_LISTENING
        self._pending_text = None  # Text waiting to be processed

        # Speaker (TTS output)
        self.speaker: SpeakerStream = (
            NullSpeakerStream() if settings.use_mock_audio else SpeakerStream()
        )

        # Microphone (audio input)
        mic_cls = MockMicrophoneStream if settings.use_mock_audio else MicrophoneStream
        self.microphone = mic_cls(self.mic_queue, loop=self.loop)

        # STT engine - pass queue directly
        self.stt = STTStream(self._on_transcript, mic_queue=self.mic_queue)

        # Barge-in detector
        self.barge_in = BargeInDetector(self.mic_queue)
        self.stop_llm_event = asyncio.Event()
        self.stop_tts_event = asyncio.Event()
        self.barge_in.attach_stop_event(self.stop_llm_event)
        self.barge_in.attach_stop_event(self.stop_tts_event)
        self.barge_in.set_loop(self.loop)

        self._stack = AsyncExitStack()

    # ----------------------------
    # HANDLE TRANSCRIPTS
    # ----------------------------
    def _on_transcript(self, text: str, is_final: bool) -> None:
        if not text:
            return
        print(f"[STT] {'FINAL' if is_final else 'PARTIAL'}: {text}")

        # Only final messages get sent to the LLM
        if not is_final:
            return

        # Queue the text for processing
        self._pending_text = text

    # ----------------------------
    # LLM + TTS HANDLING
    # ----------------------------
    async def _handle_user_text(self, text: str) -> None:
        print(f"[AGENT] Processing: {text}")
        self._set_state(STATE_THINKING)
        self.stop_llm_event.clear()
        self.stop_tts_event.clear()
        self.speaker.clear()

        async def token_generator():
            token_queue: asyncio.Queue[str | None] = asyncio.Queue()

            def on_token(token: str) -> None:
                token_queue.put_nowait(token)

            async def run_llm():
                await llm_stream(text, on_token, stop_event=self.stop_llm_event)
                token_queue.put_nowait(None)  # Signal end

            llm_task = asyncio.create_task(run_llm())
            
            try:
                while True:
                    token = await token_queue.get()
                    if token is None:  # LLM finished
                        break
                    yield token
            finally:
                await llm_task

        self._set_state(STATE_SPEAKING)
        # Don't pause STT completely - allow barge-in detection
        self.stt.paused = True  # Pause transcript processing, but barge-in still works
        
        await stream_tts(
            token_generator(), self.speaker, stop_event=self.stop_tts_event
        )
        
        # Check if interrupted
        if self.barge_in.interrupted:
            print("[AGENT] Was interrupted by user")
            self.barge_in.reset()
        
        self.stt.paused = False  # Resume STT
        self._set_state(STATE_LISTENING)

    # ----------------------------
    # AGENT STATE
    # ----------------------------
    def _set_state(self, new_state: str) -> None:
        self.state = new_state
        self.barge_in.set_state(new_state)
        print(f"[STATE] -> {new_state}")

    # ----------------------------
    # STARTUP
    # ----------------------------
    async def _start_background(self) -> None:
        self.speaker.start()
        self.microphone.start()
        self.stt.start()
        self.barge_in.start()  # Start barge-in detector thread

    async def run(self, runtime: Optional[float] = None) -> None:
        """Run the agent. Pass runtime to auto-stop after N seconds."""
        await self._start_background()
        print("Agent is running. Speak into your mic.")
        try:
            if runtime:
                await asyncio.sleep(runtime)
            else:
                while True:
                    # Check for pending text to process
                    if self._pending_text:
                        text = self._pending_text
                        self._pending_text = None
                        await self._handle_user_text(text)
                    await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping agent...")
        finally:
            self.stop()

    # ----------------------------
    # CLEANUP
    # ----------------------------
    def stop(self) -> None:
        self.stop_llm_event.set()
        self.stop_tts_event.set()
        self.barge_in.stop()
        self.stt.stop()
        self.microphone.stop()
        self.speaker.stop()


# Make sure this is defined AFTER the class exists
AgentApp.instance = None


def main():  # pragma: no cover - entrypoint
    app = AgentApp()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
