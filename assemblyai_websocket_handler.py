"""
AssemblyAI WebSocket Handler - Real-time streaming transcription using official SDK
Uses Universal Streaming API for low latency transcription
"""
import asyncio
import logging
from typing import Callable, Type
import io
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingParameters,
    StreamingEvents,
    BeginEvent,
    TurnEvent,
    TerminationEvent,
    StreamingError
)

logger = logging.getLogger("AssemblyAI-SDK")

class AudioStreamIterator:
    """Iterator to stream audio chunks from queue to AssemblyAI SDK"""
    def __init__(self, audio_queue):
        self.audio_queue = audio_queue
        self._closed = False
        self._buffer = b''
        # AssemblyAI requires 50-1000ms chunks
        # At 16kHz mu-law: 16000 bytes/sec, so 50ms = 800 bytes minimum
        self.min_chunk_size = 800  # 50ms at 16kHz
        
    def __iter__(self):
        return self
        
    def __next__(self):
        """Get next audio chunk - buffer to meet 50ms minimum"""
        if self._closed:
            raise StopIteration
            
        try:
            import queue
            
            # Accumulate audio until we have at least 50ms worth
            while len(self._buffer) < self.min_chunk_size:
                try:
                    # Block waiting for audio with longer timeout
                    audio_chunk = self.audio_queue.get(timeout=1.0)
                    
                    if audio_chunk is None:  # Signal to close
                        self._closed = True
                        # Flush any remaining buffer
                        if len(self._buffer) >= self.min_chunk_size:
                            result = self._buffer
                            self._buffer = b''
                            return result
                        # If less than minimum, discard and stop
                        raise StopIteration
                    
                    self._buffer += audio_chunk
                    
                except queue.Empty:
                    # Timeout waiting for audio
                    # If we have at least minimum, send it
                    if len(self._buffer) >= self.min_chunk_size:
                        result = self._buffer
                        self._buffer = b''
                        return result
                    # Otherwise keep waiting - NEVER return empty bytes
                    continue
            
            # We have enough buffered - send it
            result = self._buffer
            self._buffer = b''
            
            # Log first 5 chunks, then every 20th
            if not hasattr(self, '_chunk_count'):
                self._chunk_count = 0
            self._chunk_count += 1
            if self._chunk_count <= 5 or self._chunk_count % 20 == 0:
                logger.info(f"🎤 Sending buffered chunk #{self._chunk_count} to AssemblyAI ({len(result)} bytes)")
            
            return result
            
        except:
            raise StopIteration
    
    def close(self):
        self._closed = True

class AssemblyAIWebSocketHandler:
    """Real-time transcription using AssemblyAI Universal Streaming via official SDK"""
    
    def __init__(self, api_key: str, on_transcript: Callable, call_uuid: str):
        self.api_key = api_key
        self.on_transcript = on_transcript
        self.call_uuid = call_uuid
        self.client = None
        self.is_connected = False
        # Use synchronous queue for iterator
        import queue
        self.audio_queue = queue.Queue()
        self._stream_task = None
        self.session_id = None
        # Store event loop for thread-safe async calls
        self.loop = asyncio.get_event_loop()
        
    def _on_begin(self, client, event: BeginEvent):
        """Called when streaming session starts"""
        self.session_id = event.id
        logger.info(f"[{self.call_uuid}] ✅ Streaming session started: {event.id}")
    
    def _on_turn(self, client, event: TurnEvent):
        """Called when we get transcript updates - runs in SDK's background thread"""
        transcript = event.transcript.strip()
        
        if transcript:
            logger.info(f"[{self.call_uuid}] 📝 Transcript: '{transcript}' (end_of_turn={event.end_of_turn}, confidence={event.end_of_turn_confidence:.2f})")
            
            # For voice agents, trigger on end_of_turn for low latency
            if event.end_of_turn:
                logger.info(f"[{self.call_uuid}] ✅ End of turn detected, sending transcript")
                # Call the callback in the main event loop (thread-safe)
                asyncio.run_coroutine_threadsafe(
                    self.on_transcript(transcript),
                    self.loop
                )
    
    def _on_terminated(self, client, event: TerminationEvent):
        """Called when session terminates"""
        logger.info(f"[{self.call_uuid}] Session terminated: {event.audio_duration_seconds}s of audio processed")
        self.is_connected = False
    
    def _on_error(self, client, error: StreamingError):
        """Called on errors"""
        logger.error(f"[{self.call_uuid}] ❌ Streaming error: {error}")
        self.is_connected = False
        
    async def connect(self):
        """Connect to AssemblyAI Universal Streaming API using official SDK"""
        try:
            logger.info(f"[{self.call_uuid}] Connecting to AssemblyAI Universal Streaming (SDK)...")
            
            # Create streaming client
            self.client = StreamingClient(
                StreamingClientOptions(
                    api_key=self.api_key,
                    api_host="streaming.assemblyai.com",
                )
            )
            
            # Set up event handlers
            self.client.on(StreamingEvents.Begin, self._on_begin)
            self.client.on(StreamingEvents.Turn, self._on_turn)
            self.client.on(StreamingEvents.Termination, self._on_terminated)
            self.client.on(StreamingEvents.Error, self._on_error)
            
            # Connect with parameters
            # Phone audio is 8kHz mu-law, no formatting for lowest latency
            self.client.connect(
                StreamingParameters(
                    sample_rate=16000,  # Vonage sends 16kHz audio
                    encoding="pcm_mulaw",
                    format_turns=False,  # Disable formatting for lower latency
                )
            )
            
            self.is_connected = True
            logger.info(f"[{self.call_uuid}] ✅ Connected to AssemblyAI Universal Streaming")
            
            # Start audio streaming task
            self._stream_task = asyncio.create_task(self._stream_audio())
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Failed to connect to AssemblyAI: {e}")
            logger.exception(e)
            self.is_connected = False
            return False
    
    async def _stream_audio(self):
        """Stream audio from queue to AssemblyAI"""
        try:
            logger.info(f"[{self.call_uuid}] Starting audio stream...")
            
            # Create audio stream iterator
            audio_stream = AudioStreamIterator(self.audio_queue)
            
            # Stream audio to AssemblyAI (runs in background thread)
            self.client.stream(audio_stream)
            
            logger.info(f"[{self.call_uuid}] Audio streaming completed")
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Error streaming audio: {e}")
            logger.exception(e)
            self.is_connected = False
    
    async def send_audio(self, audio_data: bytes):
        """
        Send audio data to AssemblyAI
        
        Args:
            audio_data: μ-law encoded audio bytes from phone
        """
        if not self.is_connected:
            return
            
        try:
            # Put audio in queue for streaming (synchronous queue)
            self.audio_queue.put_nowait(audio_data)
            # Log first 10 chunks, then every 50th
            if not hasattr(self, '_audio_count'):
                self._audio_count = 0
            self._audio_count += 1
            if self._audio_count <= 10 or self._audio_count % 50 == 0:
                logger.info(f"[{self.call_uuid}] 📥 Queued audio chunk #{self._audio_count} ({len(audio_data)} bytes) to AssemblyAI")
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Error sending audio: {e}")
    
    async def close(self):
        """Close the connection"""
        logger.info(f"[{self.call_uuid}] Closing AssemblyAI connection...")
        
        try:
            self.is_connected = False
            
            # Signal end of audio
            self.audio_queue.put_nowait(None)
            
            # Wait for stream task to finish
            if self._stream_task:
                await asyncio.wait_for(self._stream_task, timeout=5.0)
            
            # Disconnect client
            if self.client:
                self.client.disconnect(terminate=True)
                
            logger.info(f"[{self.call_uuid}] ✅ AssemblyAI connection closed")
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error closing connection: {e}")
