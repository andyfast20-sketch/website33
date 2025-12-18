"""
AssemblyAI REST API Handler - WORKING METHOD
Uses async transcription with chunked audio buffering and VAD
Optimized for UK accents
"""
import asyncio
import httpx
import logging
import wave
import io
import numpy as np
from typing import Callable, Optional

logger = logging.getLogger("AssemblyAI-REST")

class AssemblyAIRestHandler:
    """Handle AssemblyAI transcription via REST API (working!)"""
    
    def __init__(self, api_key: str, on_transcript: Callable, call_uuid: str):
        self.api_key = api_key
        self.on_transcript = on_transcript
        self.call_uuid = call_uuid
        self.audio_buffer = bytearray()
        self.is_active = True
        self.processing = False
        self.min_chunk_size = 96000  # 3 seconds at 16kHz * 2 bytes
        self.max_chunk_size = 192000  # 6 seconds max - faster processing
        self.silence_threshold = 200  # Lower threshold for phone audio (was 500)
        self.has_speech = False
        self.silence_duration = 0  # Track silence duration
        self.silence_frames_needed = 12  # ~0.4 seconds of silence at 20ms chunks
    
    def _pcm_to_wav(self, pcm_data):
        """Convert raw PCM to WAV format"""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(pcm_data)
        return wav_buffer.getvalue()
        
    async def add_audio(self, audio_bytes: bytes):
        """Add audio to buffer and transcribe when enough accumulated"""
        if not self.is_active:
            return
        
        # Check if this chunk contains speech using Voice Activity Detection
        try:
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array.astype(np.float32)**2))
            
            if rms > self.silence_threshold:
                self.has_speech = True
                self.silence_duration = 0  # Reset silence counter
            else:
                self.silence_duration += 1  # Increment silence counter
        except:
            # If VAD fails, assume speech is present
            self.has_speech = True
            
        self.audio_buffer.extend(audio_bytes)
        
        # Process buffer when:
        # 1. We have minimum audio AND speech detected AND silence pause detected
        # 2. OR we've exceeded maximum buffer size (don't wait forever)
        should_process = False
        
        if len(self.audio_buffer) >= self.max_chunk_size:
            # Too much audio - process now
            should_process = True
            logger.info(f"[{self.call_uuid}] Max buffer reached ({len(self.audio_buffer)} bytes) - processing...")
        elif (len(self.audio_buffer) >= self.min_chunk_size and 
              self.has_speech and 
              self.silence_duration >= self.silence_frames_needed):
            # Good amount of audio + speech detected + pause after speaking
            should_process = True
            logger.info(f"[{self.call_uuid}] Speech pause detected ({len(self.audio_buffer)} bytes) - processing...")
        
        if should_process and not self.processing:
            await self._process_buffer()
    
    async def _process_buffer(self):
        """Process accumulated audio buffer"""
        if self.processing or len(self.audio_buffer) == 0:
            return
        
        self.processing = True
        
        try:
            # Take current buffer
            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()
            self.has_speech = False  # Reset speech flag
            self.silence_duration = 0  # Reset silence counter
            
            # Convert to WAV format
            wav_data = self._pcm_to_wav(audio_data)
            logger.info(f"[{self.call_uuid}] Processing {len(audio_data)} bytes PCM -> {len(wav_data)} bytes WAV...")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Step 1: Upload audio
                upload_response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"Authorization": self.api_key},
                    content=wav_data
                )
                
                if upload_response.status_code != 200:
                    logger.error(f"[{self.call_uuid}] Upload failed: {upload_response.status_code}")
                    return
                
                audio_url = upload_response.json()["upload_url"]
                
                # Step 2: Create transcript with UK English model
                transcript_response = await client.post(
                    "https://api.assemblyai.com/v2/transcript",
                    headers={"Authorization": self.api_key},
                    json={
                        "audio_url": audio_url,
                        "language_code": "en_uk",  # UK English for better accent recognition
                        "speech_model": "best"  # Use best model for accuracy
                    }
                )
                
                if transcript_response.status_code != 200:
                    logger.error(f"[{self.call_uuid}] Transcript failed: {transcript_response.status_code}")
                    return
                
                transcript_id = transcript_response.json()["id"]
                
                # Step 3: Poll for result (max 5 seconds)
                for _ in range(10):  # 10 attempts * 0.5s = 5s max
                    await asyncio.sleep(0.5)
                    
                    result_response = await client.get(
                        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                        headers={"Authorization": self.api_key}
                    )
                    
                    if result_response.status_code != 200:
                        continue
                    
                    result = result_response.json()
                    status = result.get("status")
                    
                    if status == "completed":
                        text = result.get("text", "").strip()
                        if text:
                            logger.info(f"[{self.call_uuid}] 📝 Transcribed: {text}")
                            await self.on_transcript(text)
                        else:
                            logger.warning(f"[{self.call_uuid}] ⚠️ Empty transcript - no speech detected in audio")
                        break
                    elif status == "error":
                        logger.error(f"[{self.call_uuid}] Transcription error: {result.get('error')}")
                        break
                
        except Exception as e:
            logger.error(f"[{self.call_uuid}] Processing error: {e}")
        finally:
            self.processing = False
    
    async def flush(self):
        """Process any remaining audio in buffer"""
        if len(self.audio_buffer) > 0:
            await self._process_buffer()
    
    def close(self):
        """Stop processing"""
        self.is_active = False
