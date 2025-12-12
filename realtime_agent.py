"""
Voice Agent using OpenAI Realtime API
This is the proper way to do voice assistants - one streaming connection
that handles speech recognition, thinking, and voice output seamlessly.
"""
import asyncio
import base64
import json
import sounddevice as sd
import numpy as np
from scipy import signal
from websockets import connect

OPENAI_API_KEY = "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"

# Audio settings
INPUT_RATE = 44100  # Jabra's native rate
OUTPUT_RATE = 24000  # Realtime API uses 24kHz PCM16
CHANNELS = 1

class RealtimeVoiceAgent:
    def __init__(self):
        self.ws = None
        self.audio_buffer = []
        self.is_playing = False
        self.output_stream = None
        
    async def connect(self):
        """Connect to OpenAI Realtime API"""
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        print("[AGENT] Connecting to OpenAI Realtime API...")
        self.ws = await connect(url, additional_headers=headers)
        print("[AGENT] Connected!")
        
        # Configure the session
        await self.ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful voice assistant. Keep responses brief and conversational.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }))
        print("[AGENT] Session configured with server-side VAD")
        
    async def send_audio(self):
        """Capture and send audio to the API"""
        print("[MIC] Starting microphone capture...")
        
        # Use WASAPI Jabra device (19)
        device = 19
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"[MIC] Status: {status}")
            # Store raw audio
            self.audio_buffer.extend(indata[:, 0].copy())
        
        # Open input stream at Jabra's native 44100Hz
        with sd.InputStream(
            device=device,
            samplerate=INPUT_RATE,
            channels=CHANNELS,
            dtype='float32',
            blocksize=int(INPUT_RATE * 0.1),  # 100ms chunks
            callback=audio_callback
        ):
            print("[MIC] Microphone opened! Speak now...")
            
            while True:
                # Process ~100ms of audio at 44100Hz
                chunk_size = int(INPUT_RATE * 0.1)
                if len(self.audio_buffer) >= chunk_size:
                    audio_chunk = np.array(self.audio_buffer[:chunk_size])
                    self.audio_buffer = self.audio_buffer[chunk_size:]
                    
                    # Resample from 44100Hz to 24000Hz
                    num_samples = int(len(audio_chunk) * OUTPUT_RATE / INPUT_RATE)
                    resampled = signal.resample(audio_chunk, num_samples)
                    
                    # Convert to int16 PCM
                    audio_int16 = (resampled * 32767).astype(np.int16)
                    
                    # Send audio to API
                    await self.ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(audio_int16.tobytes()).decode()
                    }))
                
                await asyncio.sleep(0.05)
    
    async def receive_responses(self):
        """Receive and play audio responses"""
        print("[AGENT] Listening for responses...")
        
        # Open output stream at 24kHz
        self.output_stream = sd.OutputStream(
            samplerate=OUTPUT_RATE,
            channels=CHANNELS,
            dtype='int16'
        )
        self.output_stream.start()
        
        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type", "")
                
                if event_type == "session.created":
                    print("[AGENT] Session created successfully")
                    
                elif event_type == "session.updated":
                    print("[AGENT] Session updated")
                    
                elif event_type == "input_audio_buffer.speech_started":
                    print("[AGENT] Speech detected...")
                    
                elif event_type == "input_audio_buffer.speech_stopped":
                    print("[AGENT] Speech ended, processing...")
                    
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    print(f"[YOU] {transcript}")
                    
                elif event_type == "response.audio.delta":
                    # Play audio chunk
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                        self.output_stream.write(audio_array)
                        
                elif event_type == "response.audio_transcript.delta":
                    # Print what the assistant is saying
                    text = event.get("delta", "")
                    print(text, end="", flush=True)
                    
                elif event_type == "response.audio_transcript.done":
                    print()  # New line after response
                    
                elif event_type == "response.done":
                    print("[AGENT] Response complete")
                    
                elif event_type == "error":
                    print(f"[ERROR] {event.get('error', {}).get('message', 'Unknown error')}")
                    
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
    
    async def run(self):
        """Main run loop"""
        await self.connect()
        
        # Run send and receive concurrently
        await asyncio.gather(
            self.send_audio(),
            self.receive_responses()
        )

async def main():
    print("=" * 50)
    print("OpenAI Realtime Voice Agent")
    print("=" * 50)
    print("This uses OpenAI's Realtime API for seamless")
    print("speech-to-speech conversation.")
    print("Press Ctrl+C to exit.")
    print("=" * 50)
    
    agent = RealtimeVoiceAgent()
    try:
        await agent.run()
    except KeyboardInterrupt:
        print("\n[AGENT] Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
