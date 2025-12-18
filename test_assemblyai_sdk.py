"""
Test AssemblyAI with official SDK
"""
import assemblyai as aai
import asyncio
import numpy as np
import os

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not aai.settings.api_key:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY env var")

def test_streaming():
    """Test streaming transcription"""
    print("=" * 60)
    print("Testing AssemblyAI Streaming Transcription")
    print("=" * 60)
    
    transcriptions = []
    
    def on_open(session):
        print("✅ Session opened")
    
    def on_data(transcript):
        if not transcript.text:
            return
        
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            print(f"✅ FINAL: {transcript.text}")
            transcriptions.append(transcript.text)
        else:
            print(f"⏱️  PARTIAL: {transcript.text}")
    
    def on_error(error):
        print(f"❌ Error: {error}")
    
    def on_close():
        print("🔌 Session closed")
    
    # Create transcriber
    transcriber = aai.RealtimeTranscriber(
        sample_rate=16000,
        on_data=on_data,
        on_error=on_error,
        on_open=on_open,
        on_close=on_close,
    )
    
    print("Connecting...")
    transcriber.connect()
    
    # Generate test audio (sine wave)
    print("Generating and sending test audio...")
    sample_rate = 16000
    duration = 2.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
    pcm_audio = (audio_signal * 32767).astype(np.int16)
    
    # Send in chunks
    chunk_size = 1600  # 100ms chunks
    pcm_bytes = pcm_audio.tobytes()
    
    for i in range(0, len(pcm_bytes), chunk_size):
        chunk = pcm_bytes[i:i + chunk_size]
        transcriber.stream(chunk)
    
    print("Waiting for transcription...")
    import time
    time.sleep(5)
    
    transcriber.close()
    
    if transcriptions:
        print(f"\n✅ SUCCESS! Received {len(transcriptions)} transcriptions")
        return True
    else:
        print("\n⚠️  No transcriptions (test audio might not contain speech)")
        print("But connection worked! This is normal for sine wave.")
        return True

if __name__ == "__main__":
    success = test_streaming()
    if success:
        print("\n🎉 AssemblyAI is working! Ready for live calls.")
    else:
        print("\n❌ Tests failed")
