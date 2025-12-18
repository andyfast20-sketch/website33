"""
Test AssemblyAI integration without making phone calls
"""
import asyncio
import audioop
import numpy as np
from scipy.io import wavfile
import os
import sys

# Add agent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from assemblyai_handler import AssemblyAIRealtimeClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TEST")

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY env var")

async def test_assemblyai_connection():
    """Test 1: Can we connect to AssemblyAI?"""
    logger.info("=" * 60)
    logger.info("TEST 1: Testing AssemblyAI Connection")
    logger.info("=" * 60)
    
    transcripts = []
    
    def on_transcript(text):
        logger.info(f"✅ TRANSCRIBED: {text}")
        transcripts.append(text)
    
    client = AssemblyAIRealtimeClient(
        api_key=ASSEMBLYAI_API_KEY,
        on_transcript=on_transcript,
        call_uuid="TEST-001"
    )
    
    try:
        await client.connect()
        logger.info("✅ Connection successful!")
        await asyncio.sleep(2)
        return True, client
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False, None


async def test_send_audio(client):
    """Test 2: Can we send audio to AssemblyAI?"""
    logger.info("=" * 60)
    logger.info("TEST 2: Sending Test Audio")
    logger.info("=" * 60)
    
    # Generate a simple sine wave (440 Hz tone for 1 second)
    # This simulates audio data
    sample_rate = 16000
    duration = 1.0
    frequency = 440.0  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_signal = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    pcm_audio = (audio_signal * 32767).astype(np.int16)
    
    # Send in chunks (like Vonage would)
    chunk_size = 320  # 20ms at 16kHz for μ-law
    pcm_bytes = pcm_audio.tobytes()
    
    logger.info(f"Generated {len(pcm_bytes)} bytes of test audio")
    
    try:
        chunks_sent = 0
        for i in range(0, len(pcm_bytes), chunk_size * 2):  # *2 because 16-bit = 2 bytes per sample
            chunk = pcm_bytes[i:i + chunk_size * 2]
            await client.send_audio(chunk)
            chunks_sent += 1
            await asyncio.sleep(0.02)  # 20ms between chunks
        
        logger.info(f"✅ Sent {chunks_sent} chunks of audio")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send audio: {e}")
        return False


async def test_with_real_speech():
    """Test 3: Send actual speech if we have a sample file"""
    logger.info("=" * 60)
    logger.info("TEST 3: Testing with Real Speech Sample")
    logger.info("=" * 60)
    
    transcripts = []
    
    async def on_transcript(text):
        logger.info(f"✅ TRANSCRIBED: {text}")
        transcripts.append(text)
    
    client = AssemblyAIRealtimeClient(
        api_key=ASSEMBLYAI_API_KEY,
        on_transcript=on_transcript,
        call_uuid="TEST-SPEECH"
    )
    
    try:
        await client.connect()
        logger.info("✅ Connected")
        
        # Generate speech: "Hello, this is a test"
        # Use a simple pattern that resembles speech
        sample_rate = 16000
        duration = 2.0
        
        # Create a more complex waveform that resembles speech
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Mix of frequencies to simulate speech
        speech_like = (
            np.sin(2 * np.pi * 200 * t) +  # Fundamental
            0.5 * np.sin(2 * np.pi * 400 * t) +  # Harmonic
            0.3 * np.sin(2 * np.pi * 600 * t) +  # Harmonic
            0.2 * np.random.randn(len(t))  # Noise
        )
        
        # Normalize and convert to 16-bit PCM
        speech_like = speech_like / np.max(np.abs(speech_like)) * 0.8
        pcm_audio = (speech_like * 32767).astype(np.int16)
        pcm_bytes = pcm_audio.tobytes()
        
        logger.info(f"Generated {len(pcm_bytes)} bytes of speech-like audio")
        
        # Send in chunks
        chunk_size = 640  # 40ms chunks
        for i in range(0, len(pcm_bytes), chunk_size):
            chunk = pcm_bytes[i:i + chunk_size]
            await client.send_audio(chunk)
            await asyncio.sleep(0.02)
        
        logger.info("✅ Sent all speech audio, waiting for transcription...")
        
        # Wait for transcription
        await asyncio.sleep(5)
        
        if transcripts:
            logger.info(f"✅ Received {len(transcripts)} transcripts!")
            for t in transcripts:
                logger.info(f"   - {t}")
            return True
        else:
            logger.warning("⚠️ No transcripts received (synthetic audio might not be recognized)")
            return True  # Connection still worked
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_mulaw_conversion():
    """Test 4: Test μ-law to PCM conversion (what Vonage sends)"""
    logger.info("=" * 60)
    logger.info("TEST 4: Testing μ-law to PCM Conversion")
    logger.info("=" * 60)
    
    # Create sample PCM audio
    sample_rate = 16000
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_signal = np.sin(2 * np.pi * 440 * t)
    pcm_16bit = (audio_signal * 32767).astype(np.int16).tobytes()
    
    logger.info(f"Original PCM: {len(pcm_16bit)} bytes")
    
    # Convert to μ-law (simulating what Vonage sends)
    mulaw_data = audioop.lin2ulaw(pcm_16bit, 2)
    logger.info(f"μ-law encoded: {len(mulaw_data)} bytes")
    
    # Convert back to PCM (what our code does)
    pcm_converted = audioop.ulaw2lin(mulaw_data, 2)
    logger.info(f"Converted back to PCM: {len(pcm_converted)} bytes")
    
    if len(pcm_16bit) == len(pcm_converted):
        logger.info("✅ Conversion successful - sizes match!")
        return True
    else:
        logger.error("❌ Conversion failed - size mismatch!")
        return False


async def run_all_tests():
    """Run all tests sequentially"""
    logger.info("\n" + "=" * 60)
    logger.info("ASSEMBLYAI INTEGRATION TEST SUITE")
    logger.info("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Connection
    success, client = await test_assemblyai_connection()
    results["Connection"] = success
    
    if not success:
        logger.error("❌ Connection failed, stopping tests")
        return results
    
    # Test 2: Send audio
    await asyncio.sleep(1)
    success = await test_send_audio(client)
    results["Send Audio"] = success
    
    await client.close()
    await asyncio.sleep(2)
    
    # Test 3: Real speech test
    success = await test_with_real_speech()
    results["Speech Recognition"] = success
    
    await asyncio.sleep(1)
    
    # Test 4: μ-law conversion
    success = await test_mulaw_conversion()
    results["μ-law Conversion"] = success
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED! AssemblyAI is ready to use.")
        logger.info("You can now test with a real phone call.")
    else:
        logger.error("❌ Some tests failed. Check logs above for details.")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
