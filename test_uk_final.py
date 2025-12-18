"""
Quick UK Accent Verification Test
Fast test to confirm AssemblyAI + UK accents work
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

def pcm_to_wav(pcm_data):
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_data)
    return wav_buffer.getvalue()

async def test_phrase(phrase):
    """Test one phrase - fast version"""
    print(f"\nTesting: '{phrase}'")
    print("-" * 60)
    
    # Generate UK speech
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=f"Speak with a British accent: {phrase}",
        response_format="pcm"
    )
    
    # Convert 24kHz to 16kHz PCM
    audio_24k = response.content
    audio_16k = audioop.ratecv(audio_24k, 2, 1, 24000, 16000, None)[0]
    
    # Convert to WAV
    wav_data = pcm_to_wav(audio_16k)
    print(f"Audio ready: {len(wav_data)} bytes WAV")
    
    # Send to AssemblyAI with UK English
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        # Upload
        print("Uploading to AssemblyAI...")
        upload = await http_client.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"Authorization": ASSEMBLYAI_API_KEY},
            content=wav_data
        )
        
        if upload.status_code != 200:
            print(f"FAIL: Upload error {upload.status_code}")
            return False
        
        audio_url = upload.json()["upload_url"]
        print(f"Uploaded: {audio_url[:50]}...")
        
        # Create transcript with UK English
        print("Creating transcript with UK English model...")
        transcript = await http_client.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={"Authorization": ASSEMBLYAI_API_KEY},
            json={
                "audio_url": audio_url,
                "language_code": "en_uk",
                "speech_model": "best"
            }
        )
        
        transcript_id = transcript.json()["id"]
        print(f"Transcript ID: {transcript_id}")
        
        # Poll for result
        print("Waiting for transcription...")
        for attempt in range(40):  # 20 seconds max
            await asyncio.sleep(0.5)
            
            status = await http_client.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"Authorization": ASSEMBLYAI_API_KEY}
            )
            
            result = status.json()
            state = result.get("status")
            
            if state == "completed":
                text = result.get("text", "")
                confidence = result.get("confidence", 0)
                
                print(f"\nRESULT:")
                print(f"  Transcription: '{text}'")
                print(f"  Confidence: {confidence:.1%}")
                print(f"  Length: {len(text)} chars")
                
                if len(text) > 10:
                    print("  STATUS: PASS")
                    return True
                else:
                    print("  STATUS: FAIL (empty)")
                    return False
            elif state == "error":
                print(f"FAIL: {result.get('error')}")
                return False
        
        print("FAIL: Timeout")
        return False

async def main():
    print("="*60)
    print("UK ACCENT TEST - AssemblyAI with language_code: en_uk")
    print("="*60)
    
    phrases = [
        "Hello, I would like to book an appointment",
        "Good morning, what time are you open",
        "Can I schedule something for Tuesday",
        "I need to make a booking please",
        "What is your availability"
    ]
    
    results = []
    for phrase in phrases:
        try:
            success = await test_phrase(phrase)
            results.append(success)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(False)
        await asyncio.sleep(1)
    
    # Summary
    passed = sum(results)
    total = len(results)
    rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {rate:.1f}%")
    print("="*60)
    
    if rate >= 95:
        print("VERDICT: READY FOR PHONE CALLS (95%+ success)")
    elif rate >= 80:
        print("VERDICT: GOOD - Should work (80%+ success)")
    elif rate >= 60:
        print("VERDICT: NEEDS WORK (60-80% success)")
    else:
        print("VERDICT: NOT READY (<60% success)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
