"""Barge-in detection and coordination."""
from __future__ import annotations

import asyncio
import threading
import numpy as np

from .states import STATE_LISTENING, STATE_SPEAKING


class BargeInDetector:
    """Detects user speech during playback and signals interruption."""

    def __init__(self, mic_queue, *, threshold: float = 0.03):
        self.mic_queue = mic_queue
        self.threshold = threshold
        self._state = STATE_LISTENING
        self._stop_events: list[asyncio.Event] = []
        self._loop = None
        self._thread = None
        self._running = False
        self.interrupted = False  # Flag to signal interruption occurred

    def attach_stop_event(self, stop_event: asyncio.Event) -> None:
        """Register an event that should be set when barge-in occurs."""
        self._stop_events.append(stop_event)

    def set_state(self, state: str) -> None:
        self._state = state
        if state == STATE_SPEAKING:
            self.interrupted = False  # Reset on new speech

    def set_loop(self, loop) -> None:
        self._loop = loop

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_thread, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _monitor_thread(self) -> None:
        """Monitor mic for interruptions while agent is speaking."""
        consecutive_loud = 0  # Require multiple loud frames to trigger
        
        while self._running:
            try:
                # Non-blocking check
                if self.mic_queue.empty():
                    threading.Event().wait(0.01)
                    continue
                    
                pcm = self.mic_queue.get_nowait()
                
                # Only check during speaking
                if self._state != STATE_SPEAKING:
                    consecutive_loud = 0
                    continue
                    
                if pcm is None:
                    continue
                    
                energy = float(np.max(np.abs(pcm)))
                
                if energy > self.threshold:
                    consecutive_loud += 1
                    # Require 3 consecutive loud frames to avoid false triggers
                    if consecutive_loud >= 3:
                        print(f"[BARGE-IN] Detected! Energy: {energy:.3f}")
                        self.interrupted = True
                        # Signal all stop events
                        for event in self._stop_events:
                            if self._loop:
                                self._loop.call_soon_threadsafe(event.set)
                        consecutive_loud = 0
                else:
                    consecutive_loud = 0
                    
            except Exception:
                pass

    def reset(self) -> None:
        self.interrupted = False
        for event in self._stop_events:
            event.clear()
