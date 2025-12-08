"""Barge-in detection and coordination."""
from __future__ import annotations

import asyncio
import numpy as np

from .states import STATE_LISTENING, STATE_SPEAKING


class BargeInDetector:
    """Detects user speech during playback and signals interruption."""

    def __init__(self, mic_queue: asyncio.Queue, *, threshold: float = 0.02):
        self.mic_queue = mic_queue
        self.threshold = threshold
        self._listening_state = STATE_LISTENING
        self._callbacks: list[asyncio.Event] = []

    def attach_stop_event(self, stop_event: asyncio.Event) -> None:
        """Register an event that should be set when barge-in occurs."""
        self._callbacks.append(stop_event)

    def set_state(self, state: str) -> None:
        self._listening_state = state

    async def monitor(self) -> None:
        """Continuously check mic amplitude for barge-in during speaking."""
        while True:
            pcm = await self.mic_queue.get()
            if self._listening_state != STATE_SPEAKING:
                continue
            if pcm is None:
                continue
            energy = float(np.max(np.abs(pcm)))
            if energy > self.threshold:
                for event in self._callbacks:
                    event.set()

    def reset(self) -> None:
        for event in self._callbacks:
            event.clear()
