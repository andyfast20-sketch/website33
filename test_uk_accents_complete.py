"""
Complete UK Accent Testing with AssemblyAI
Tests realistic phone call scenarios with UK accents
Goal: 95%+ certainty before real phone testing
"""
import asyncio
import audioop
import wave
import io
import httpx
import os
from openai import OpenAI

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    raise RuntimeError("Missing ASSEMBLYAI_API_KEY env var")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY env var")

# Test results tracking
test_results = []

def pcm_to_wav(pcm_data):
    """Convert PCM to WAV"""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()

async def test_uk_phrase(test_num, phrase):
    """Test single phrase with UK accent"""
    try:
        print(f"\n[TEST {test_num}] {phrase}")
        print("-" * 80)
        
        # Generate UK accent speech
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=f"Speak with a British accent: {phrase}",
            response_format="pcm"
        )
        
        audio_24k = response.content
        print(f"  Generated: {len(audio_24k)} bytes")
        
        # Convert to phone quality (8kHz)
        audio_8k = audioop.ratecv(audio_24k, 2, 1, 24000, 8000, None)[0]
        
        # Convert to u-law (Vonage format)
        audio_ulaw = audioop.lin2ulaw(audio_8k, 2)
        
        # Split into 320-byte chunks (20ms each - realistic phone)
        chunks = [audio_ulaw[i:i+320] for i in range(0, len(audio_ulaw), 320)]
        print(f"  Phone chunks: {len(chunks)} x 320 bytes")
        
        # Process like real phone call
        pcm_buffer = bytearray()
        transcripts = []
        
        for i, ulaw_chunk in enumerate(chunks):
            # Convert u-law to PCM
            pcm_chunk = audioop.ulaw2lin(ulaw_chunk, 2)
            # Upsample to 16kHz
            pcm_16k = audioop.ratecv(pcm_chunk, 2, 1, 8000, 16000, None)[0]
            pcm_buffer.extend(pcm_16k)
            
            # Process every 5 seconds (160000 bytes at 16kHz)
            if len(pcm_buffer) >= 160000:
                print(f"  Processing buffer: {len(pcm_buffer)} bytes...")
                
                audio_to_send = bytes(pcm_buffer)
                pcm_buffer.clear()
                
                wav_data = pcm_to_wav(audio_to_send)
                
                # Send to AssemblyAI
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    # Upload
                    upload_resp = await http_client.post(
                        "https://api.assemblyai.com/v2/upload",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        content=wav_data
                    )
                    
                    if upload_resp.status_code != 200:
                        print(f"  FAIL: Upload error {upload_resp.status_code}")
                        return False
                    
                    audio_url = upload_resp.json()["upload_url"]
                    
                    # Create transcript with UK English
                    transcript_resp = await http_client.post(
                        "https://api.assemblyai.com/v2/transcript",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        json={
                            "audio_url": audio_url,
                            "language_code": "en_uk",
                            "speech_model": "best"
                        }
                    )
                    
                    transcript_id = transcript_resp.json()["id"]
                    
                    # Poll for result
                    for attempt in range(20):
                        await asyncio.sleep(0.5)
                        
                        status_resp = await http_client.get(
                            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                            headers={"Authorization": ASSEMBLYAI_API_KEY}
                        )
                        
                        result = status_resp.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            text = result.get("text", "")
                            if text:
                                transcripts.append(text)
                                print(f"  TRANSCRIPT: '{text}'")
                            break
                        elif status == "error":
                            print(f"  FAIL: Transcription error")
                            return False
        
        # Process final buffer
        if len(pcm_buffer) > 16000:
            print(f"  Processing final: {len(pcm_buffer)} bytes...")
            wav_data = pcm_to_wav(bytes(pcm_buffer))
            
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                upload_resp = await http_client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"Authorization": ASSEMBLYAI_API_KEY},
                    content=wav_data
                )
                
                if upload_resp.status_code == 200:
                    audio_url = upload_resp.json()["upload_url"]
                    
                    transcript_resp = await http_client.post(
                        "https://api.assemblyai.com/v2/transcript",
                        headers={"Authorization": ASSEMBLYAI_API_KEY},
                        json={
                            "audio_url": audio_url,
                            "language_code": "en_uk",
                            "speech_model": "best"
                        }
                    )
                    
                    transcript_id = transcript_resp.json()["id"]
                    
                    for attempt in range(20):
                        await asyncio.sleep(0.5)
                        
                        status_resp = await http_client.get(
                            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                            headers={"Authorization": ASSEMBLYAI_API_KEY}
                        )
                        
                        result = status_resp.json()
                        status = result.get("status")
                        
                        if status == "completed":
                            text = result.get("text", "")
                            if text:
                                transcripts.append(text)
                                print(f"  FINAL TRANSCRIPT: '{text}'")
                            break
        
        # Check if we got transcription
        full_transcript = " ".join(transcripts)
        
        if len(full_transcript) > 10:
            print(f"  PASS: Got {len(full_transcript)} chars of transcription")
            test_results.append({
                "test": test_num,
                "phrase": phrase,
                "transcript": full_transcript,
                "success": True
            })
            return True
        else:
            print(f"  FAIL: Empty or too short transcription")
            test_results.append({
                "test": test_num,
                "phrase": phrase,
                "transcript": full_transcript,
                "success": False
            })
            return False
            
    except Exception as e:
        print(f"  FAIL: {e}")
        test_results.append({
            "test": test_num,
            "phrase": phrase,
            "error": str(e),
            "success": False
        })
        return False

async def main():
    """Run comprehensive UK accent tests"""
    print("=" * 80)
    print("COMPREHENSIVE UK ACCENT TEST - AssemblyAI")
    print("Testing realistic phone call simulation with UK English")
    print("=" * 80)
    
    # Test phrases covering different scenarios
    test_phrases = [
        "Hello, I would like to book an appointment please",
        "Good morning, what time are you open today",
        "Can I schedule something for next Tuesday",
        "I need to make a booking for two people",
        "What is your availability this week",
        "I would like to cancel my appointment",
        "Could you tell me your opening hours",
        "I need to reschedule my booking for Friday",
    ]
    
    print(f"\nRunning {len(test_phrases)} tests with UK accents...\n")
    
    passed = 0
    failed = 0
    
    for i, phrase in enumerate(test_phrases, 1):
        result = await test_uk_phrase(i, phrase)
        if result:
            passed += 1
        else:
            failed += 1
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    # Calculate success rate
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print("=" * 80)
    
    # Detailed results
    print("\nDETAILED RESULTS:")
    print("-" * 80)
    for result in test_results:
        if result["success"]:
            print(f"[PASS] Test {result['test']}: {result['phrase']}")
            print(f"       Transcript: {result['transcript'][:100]}...")
        else:
            print(f"[FAIL] Test {result['test']}: {result['phrase']}")
            if "error" in result:
                print(f"       Error: {result['error']}")
    
    print("\n" + "=" * 80)
    if success_rate >= 95:
        print(f"SUCCESS: {success_rate:.1f}% success rate - READY FOR REAL PHONE CALLS")
    elif success_rate >= 80:
        print(f"GOOD: {success_rate:.1f}% success rate - Should work but may need tuning")
    else:
        print(f"FAIL: {success_rate:.1f}% success rate - NOT READY")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
