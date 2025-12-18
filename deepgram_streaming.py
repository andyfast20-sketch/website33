"""
Deepgram WebSocket Streaming Handler - NEW APPROACH
Completely different architecture for real-time audio streaming
"""
import asyncio
import json
import logging
import websockets
from typing import Optional, Callable

logger = logging.getLogger("DeepgramStreaming")

class DeepgramStreamingClient:
    """Handle real-time audio streaming to Deepgram WebSocket"""
    
    def __init__(self, api_key: str, on_transcript: Callable, call_uuid: str):
        self.api_key = api_key
        self.on_transcript = on_transcript  # Callback when we get a transcript
        self.call_uuid = call_uuid
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.listen_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Connect to Deepgram WebSocket"""
        try:
            # Deepgram WebSocket URL with parameters
            url = (
                f"wss://api.deepgram.com/v1/listen?"
                f"encoding=linear16&"
                f"sample_rate=16000&"
                f"channels=1&"
                f"model=nova-2&"
                f"language=en&"
                f"smart_format=true&"
                f"interim_results=false&"
                f"endpointing=500"  # End of speech detection (500ms)
            )
            
            logger.info(f"[{self.call_uuid}] 🔌 Connecting to Deepgram WebSocket...")
            
            self.ws = await websockets.connect(
                url,
                extra_headers={"Authorization": f"Token {self.api_key}"},
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=5
            )
            
            self.is_connected = True
            logger.info(f"[{self.call_uuid}] ✅ Connected to Deepgram WebSocket")
            
            # Start listening for responses
            self.listen_task = asyncio.create_task(self._listen())
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Failed to connect to Deepgram: {e}")
            self.is_connected = False
            raise
    
    async def send_audio(self, audio_bytes: bytes):
        """Send audio chunk to Deepgram"""
        if self.ws and self.is_connected:
            try:
                await self.ws.send(audio_bytes)
            except Exception as e:
                logger.error(f"[{self.call_uuid}] Error sending audio to Deepgram: {e}")
                self.is_connected = False
    
    async def _listen(self):
        """Listen for transcription results from Deepgram"""
        try:
            while self.is_connected and self.ws:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=60.0)
                    
                    if isinstance(message, str):
                        data = json.loads(message)
                        
                        # Check for transcript
                        if data.get("type") == "Results":
                            channel = data.get("channel", {})
                            alternatives = channel.get("alternatives", [])
                            if alternatives:
                                transcript = alternatives[0].get("transcript", "").strip()
                                is_final = data.get("is_final", False)
                                speech_final = data.get("speech_final", False)
                                
                                # Only process final transcripts with actual content
                                if transcript and (is_final or speech_final):
                                    logger.info(f"[{self.call_uuid}] 📝 Deepgram transcript: {transcript}")
                                    # Call the callback with the transcript
                                    asyncio.create_task(self.on_transcript(transcript))
                        
                        elif data.get("type") == "Metadata":
                            logger.info(f"[{self.call_uuid}] 📊 Deepgram metadata received")
                        
                        elif data.get("type") == "Error":
                            logger.error(f"[{self.call_uuid}] ❌ Deepgram error: {data}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.call_uuid}] ⏱️ No message from Deepgram for 60s")
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"[{self.call_uuid}] 🔌 Deepgram connection closed")
                    self.is_connected = False
                    break
                except Exception as e:
                    logger.error(f"[{self.call_uuid}] Error receiving from Deepgram: {e}")
                    
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error in Deepgram listen loop: {e}")
        finally:
            self.is_connected = False
    
    async def close(self):
        """Close the Deepgram WebSocket connection"""
        try:
            self.is_connected = False
            
            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
            
            if self.ws:
                # Send close frame
                try:
                    await self.ws.send(json.dumps({"type": "CloseStream"}))
                except:
                    pass
                
                await self.ws.close()
                logger.info(f"[{self.call_uuid}] 🔌 Deepgram connection closed")
                
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error closing Deepgram connection: {e}")
