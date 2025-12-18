"""
Test AssemblyAI with realistic phone call simulation
Sends audio in small chunks exactly like Vonage does
"""
import asyncio
import audioop
import wave
import io
import httpx
import os
from openai import OpenAI

# AssemblyAI API key
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY env var")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY env var")

def pcm_to_wav(pcm_data):
    """Convert raw PCM to WAV format"""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(16000)  # 16kHz
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()

async def test_with_uk_accent(test_number, phrase, accent_instruction):
    """Test with different UK accent variations"""
    print(f"\n{'='*80}")
    print(f"TEST {test_number}: {phrase}")
    print(f"Accent: {accent_instruction}")
    print('='*80)
    
    try:
        # Generate speech with OpenAI TTS
        print("🎤 Generating speech with UK accent...")
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",  # Male voice
            input=f"{accent_instruction}: {phrase}",
            response_format="pcm"
        )
        
        # Get raw PCM audio (24kHz)
        audio_24k = response.content
        print(f"✅ Generated {len(audio_24k)} bytes of PCM audio (24kHz)")
        
        # Convert 24kHz to 8kHz (phone quality)
        audio_8k = audioop.ratecv(audio_24k, 2, 1, 24000, 8000, None)[0]
        print(f"✅ Converted to 8kHz: {len(audio_8k)} bytes (phone quality)")
        
        # Convert to μ-law (how Vonage sends it)
        audio_ulaw = audioop.lin2ulaw(audio_8k, 2)
        print(f"✅ Converted to μ-law: {len(audio_ulaw)} bytes (Vonage format)")
        
        # Now simulate phone chunks - Vonage sends ~320 bytes every 20ms
        chunk_size = 320  # 20ms of audio at 8kHz
        chunks = [audio_ulaw[i:i+chunk_size] for i in range(0, len(audio_ulaw), chunk_size)]
        print(f"✅ Split into {len(chunks)} chunks of ~{chunk_size} bytes (realistic phone streaming)")
        
        # Buffer to accumulate chunks (like our handler does)
        pcm_buffer = bytearray()
        
        print("\n📞 Simulating phone call - processing chunks in real-time...")
        for i, ulaw_chunk in enumerate(chunks):
            # Convert μ-law back to PCM 16-bit (what our handler does)
            pcm_chunk = audioop.ulaw2lin(ulaw_chunk, 2)
            
            # Convert 8kHz to 16kHz (what our handler does)
            pcm_16k = audioop.ratecv(pcm_chunk, 2, 1, 8000, 16000, None)[0]
            
            pcm_buffer.extend(pcm_16k)
            
            # Process every 96000 bytes (3 seconds at 16kHz)
            if len(pcm_buffer) >= 96000:
                print(f"   Chunk {i+1}/{len(chunks)}: Buffer reached 3 seconds ({len(pcm_buffer)} bytes) - sending to AssemblyAI...")
                
                # Take the buffer
                audio_to_send = bytes(pcm_buffer)
                pcm_buffer.clear()
                
                # Convert to WAV
                wav_data = pcm_to_wav(audio_to_send)
                
                # Send to AssemblyAI
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    # Upload
                    upload_response = await http_client.post(
                        "https://api.assemblyai.com/v2/upload",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        content=wav_data
                    )
                    
                    if upload_response.status_code != 200:
                        print(f"❌ Upload failed: {upload_response.status_code}")
                        continue
                    
                    audio_url = upload_response.json()["upload_url"]
                    
                    # Create transcript with UK English
                    transcript_response = await http_client.post(
                        "https://api.assemblyai.com/v2/transcript",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        json={
                            "audio_url": audio_url,
                            "language_code": "en_uk",
                            "speech_model": "best"
                        }
                    )
                    
                    transcript_id = transcript_response.json()["id"]
                    
                    # Poll for result
                    for attempt in range(20):  # 10 seconds max
                        await asyncio.sleep(0.5)
                        
                        status_response = await http_client.get(
                            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                            headers={"Authorization": ASSEMBLYAI_API_KEY}
                        )
                        
                        result = status_response.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            text = result.get("text", "")
                            if text:
                                print(f"   ✅ TRANSCRIPTION: '{text}'")
                            else:
                                print(f"   ⚠️  Empty transcript (no speech detected)")
                            break
                        elif status == "error":
                            print(f"   ❌ Transcription error: {result.get('error')}")
                            break
        
        # Process any remaining audio
        if len(pcm_buffer) > 16000:  # At least 0.5 seconds
            print(f"   Processing final {len(pcm_buffer)} bytes...")
            wav_data = pcm_to_wav(bytes(pcm_buffer))
            
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                upload_response = await http_client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"Authorization": ASSEMBLYAI_API_KEY},
                    content=wav_data
                )
                
                if upload_response.status_code == 200:
                    audio_url = upload_response.json()["upload_url"]
                    
                    transcript_response = await http_client.post(
                        "https://api.assemblyai.com/v2/transcript",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        json={
                            "audio_url": audio_url,
                            "language_code": "en_uk",
                            "speech_model": "best"
                        }
                    )
                    
                    transcript_id = transcript_response.json()["id"]
                    
                    for attempt in range(20):
                        await asyncio.sleep(0.5)
                        
                        status_response = await http_client.get(
                            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                            headers={"Authorization": ASSEMBLYAI_API_KEY}
                        )
                        
                        result = status_response.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            text = result.get("text", "")
                            if text:
                                print(f"   ✅ FINAL TRANSCRIPTION: '{text}'")
                            else:
                                print(f"   ⚠️  Empty final transcript")
                            break
                        elif status == "error":
                            print(f"   ❌ Final transcription error: {result.get('error')}")
                            break
        
        print(f"✅ Test {test_number} complete!\n")
        
    except Exception as e:
        print(f"❌ Test {test_number} failed: {e}\n")

async def main():
    """Run comprehensive phone simulation tests"""
    print("\n" + "="*80)
    print("PHONE CALL SIMULATION TEST")
    print("Testing AssemblyAI with realistic phone audio chunks")
    print("="*80)
    
    # Test phrases with different UK accent variations
    tests = [
        ("Hello, I'd like to book an appointment please", "Speak with a British accent"),
        ("Good morning, what time are you open today?", "Speak with a British accent"),
        ("Can I schedule something for next Tuesday?", "Speak with a British accent"),
        ("I need to make a booking for two people", "Speak with a London accent"),
        ("What's your availability this week?", "Speak with a British English accent"),
    ]
    
    for i, (phrase, accent) in enumerate(tests, 1):
        await test_with_uk_accent(i, phrase, accent)
        await asyncio.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
