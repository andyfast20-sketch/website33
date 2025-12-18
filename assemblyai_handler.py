"""
AssemblyAI Real-time Streaming Handler
Similar architecture to OpenAI Realtime (which works)
"""
import asyncio
import json
import logging
import websockets
import base64
from typing import Optional, Callable

logger = logging.getLogger("AssemblyAI")

class AssemblyAIRealtimeClient:
    """Handle real-time audio streaming with AssemblyAI"""
    
    def __init__(self, api_key: str, on_transcript: Callable, call_uuid: str):
        self.api_key = api_key
        self.on_transcript = on_transcript
        self.call_uuid = call_uuid
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.listen_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """Connect to AssemblyAI real-time WebSocket with UNIVERSAL STREAMING API"""
        try:
            # Use universal-streaming endpoint (NEW API as of Dec 2024)
            # No sample_rate in URL - we specify it in the config message
            url = "wss://api.assemblyai.com/v2/universal-streaming/ws"
            
            logger.info(f"[{self.call_uuid}] 🔌 Connecting to AssemblyAI universal streaming...")
            
            # Connect with API key as header
            self.ws = await websockets.connect(
                url,
                additional_headers={"Authorization": self.api_key},
                ping_interval=30,
                ping_timeout=10
            )
            
            # Send configuration message
            config_message = {
                "audio_encoding": "pcm_s16le",
                "sample_rate": 16000
            }
            await self.ws.send(json.dumps(config_message))
            
            self.is_connected = True
            logger.info(f"[{self.call_uuid}] ✅ Connected to AssemblyAI")
            
            # Start listening for responses
            self.listen_task = asyncio.create_task(self._listen())
            
        except Exception as e:
            logger.error(f"[{self.call_uuid}] ❌ Failed to connect to AssemblyAI: {e}")
            self.is_connected = False
            raise
    
    async def send_audio(self, audio_bytes: bytes):
        """Send audio chunk to AssemblyAI (raw PCM bytes for universal streaming)"""
        if self.ws and self.is_connected:
            try:
                # Universal streaming expects raw audio bytes, not JSON
                await self.ws.send(audio_bytes)
            except Exception as e:
                logger.error(f"[{self.call_uuid}] Error sending audio: {e}")
                self.is_connected = False
    
    async def _listen(self):
        """Listen for transcription results"""
        try:
            while self.is_connected and self.ws:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=60.0)
                    
                    if isinstance(message, str):
                        data = json.loads(message)
                        
                        # Check message type
                        message_type = data.get("message_type")
                        
                        if message_type == "SessionBegins":
                            logger.info(f"[{self.call_uuid}] 📊 AssemblyAI session started")
                            
                        elif message_type == "PartialTranscript":
                            # Ignore partial transcripts, wait for final
                            pass
                            
                        elif message_type == "FinalTranscript":
                            transcript = data.get("text", "").strip()
                            if transcript:
                                logger.info(f"[{self.call_uuid}] 📝 AssemblyAI: {transcript}")
                                # Call the callback with the transcript
                                asyncio.create_task(self.on_transcript(transcript))
                        
                        elif message_type == "SessionTerminated":
                            logger.info(f"[{self.call_uuid}] 🔌 AssemblyAI session terminated")
                            self.is_connected = False
                            break
                            
                except asyncio.TimeoutError:
                    logger.warning(f"[{self.call_uuid}] ⏱️ No message from AssemblyAI for 60s")
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"[{self.call_uuid}] 🔌 AssemblyAI connection closed")
                    self.is_connected = False
                    break
                except Exception as e:
                    logger.error(f"[{self.call_uuid}] Error receiving: {e}")
                    
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error in listen loop: {e}")
        finally:
            self.is_connected = False
    
    async def close(self):
        """Close the AssemblyAI connection"""
        try:
            self.is_connected = False
            
            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
            
            if self.ws:
                # Send terminate message
                try:
                    await self.ws.send(json.dumps({"terminate_session": True}))
                except:
                    pass
                
                await self.ws.close()
                logger.info(f"[{self.call_uuid}] 🔌 AssemblyAI connection closed")
                
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Error closing: {e}")
