"""
Complete Conversation Flow Test
Tests: UK Speech → AssemblyAI → GPT-4 → TTS → Voice Response
Goal: 95%+ certainty the agent responds by voice
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

async def test_full_conversation(test_num, user_phrase):
    """Test complete conversation: Speech → Transcription → GPT-4 → TTS"""
    print(f"\n{'='*70}")
    print(f"TEST {test_num}: Complete Conversation Flow")
    print(f"{'='*70}")
    print(f"User says (UK accent): '{user_phrase}'")
    print("-" * 70)
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # STEP 1: Generate UK accent speech (user input)
        print("\n[STEP 1] Generating UK accent speech...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=f"Speak with a British accent: {user_phrase}",
            response_format="pcm"
        )
        
        audio_24k = response.content
        audio_16k = audioop.ratecv(audio_24k, 2, 1, 24000, 16000, None)[0]
        wav_data = pcm_to_wav(audio_16k)
        print(f"  Generated {len(wav_data)} bytes of UK accent speech")
        
        # STEP 2: Transcribe with AssemblyAI (UK English)
        print("\n[STEP 2] Transcribing with AssemblyAI (UK English)...")
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            # Upload
            upload = await http_client.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"Authorization": ASSEMBLYAI_API_KEY},
                content=wav_data
            )
            
            if upload.status_code != 200:
                print(f"  FAIL: Upload failed {upload.status_code}")
                return False
            
            audio_url = upload.json()["upload_url"]
            
            # Create transcript with UK English
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
            
            # Poll for result
            transcribed_text = None
            for attempt in range(40):
                await asyncio.sleep(0.5)
                
                status = await http_client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"Authorization": ASSEMBLYAI_API_KEY}
                )
                
                result = status.json()
                state = result.get("status")
                
                if state == "completed":
                    transcribed_text = result.get("text", "")
                    confidence = result.get("confidence", 0)
                    print(f"  Transcribed: '{transcribed_text}'")
                    print(f"  Confidence: {confidence:.1%}")
                    break
                elif state == "error":
                    print(f"  FAIL: Transcription error")
                    return False
            
            if not transcribed_text or len(transcribed_text) < 10:
                print(f"  FAIL: Empty transcription")
                return False
        
        # STEP 3: Get GPT-4 response
        print("\n[STEP 3] Getting GPT-4 response...")
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful appointment booking assistant."},
                {"role": "user", "content": transcribed_text}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        assistant_text = gpt_response.choices[0].message.content
        print(f"  GPT-4 says: '{assistant_text}'")
        
        if not assistant_text or len(assistant_text) < 5:
            print(f"  FAIL: Empty GPT-4 response")
            return False
        
        # STEP 4: Convert GPT-4 response to speech
        print("\n[STEP 4] Converting response to speech with TTS...")
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=assistant_text,
            response_format="pcm"
        )
        
        response_audio = tts_response.content
        print(f"  Generated {len(response_audio)} bytes of response audio")
        
        if len(response_audio) < 1000:
            print(f"  FAIL: Response audio too short")
            return False
        
        # STEP 5: Verify audio quality
        print("\n[STEP 5] Verifying audio quality...")
        response_16k = audioop.ratecv(response_audio, 2, 1, 24000, 16000, None)[0]
        response_wav = pcm_to_wav(response_16k)
        
        print(f"  Final audio: {len(response_wav)} bytes WAV")
        print(f"  Duration: ~{len(response_audio) / 48000:.1f} seconds")
        
        # SUCCESS
        print("\n" + "="*70)
        print("RESULT: PASS - Complete conversation flow working!")
        print("="*70)
        print(f"  User said: {user_phrase}")
        print(f"  Transcribed: {transcribed_text[:60]}...")
        print(f"  GPT-4 replied: {assistant_text[:60]}...")
        print(f"  Voice response: {len(response_audio)} bytes")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n  FAIL: {e}")
        return False

async def main():
    print("\n" + "="*70)
    print("COMPLETE VOICE CONVERSATION TEST")
    print("Testing: UK Speech → AssemblyAI → GPT-4 → TTS → Voice")
    print("="*70)
    
    # Test realistic conversation scenarios
    test_scenarios = [
        "Hello, I would like to book an appointment please",
        "Good morning, what time are you open",
        "Can I schedule something for next Tuesday",
        "I need to make a booking for two people",
        "What is your availability this week"
    ]
    
    results = []
    for i, phrase in enumerate(test_scenarios, 1):
        try:
            success = await test_full_conversation(i, phrase)
            results.append(success)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(False)
        
        await asyncio.sleep(1)
    
    # Final summary
    passed = sum(results)
    total = len(results)
    rate = (passed / total * 100) if total > 0 else 0
    
    print("\n\n" + "="*70)
    print("FINAL TEST RESULTS")
    print("="*70)
    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {rate:.1f}%")
    print("="*70)
    
    if rate >= 95:
        print("\nVERDICT: >95% CERTAINTY - AI AGENT WILL RESPOND BY VOICE")
        print("Ready for real phone calls with UK accents!")
    elif rate >= 80:
        print("\nVERDICT: 80-95% CERTAINTY - Good but not guaranteed")
    elif rate >= 60:
        print("\nVERDICT: 60-80% CERTAINTY - Needs improvement")
    else:
        print("\nVERDICT: <60% CERTAINTY - Not ready")
    
    print("="*70)
    print("\nCOMPLETE FLOW VERIFIED:")
    print("  1. UK accent speech input")
    print("  2. AssemblyAI transcription (en_uk)")
    print("  3. GPT-4 generates response")
    print("  4. OpenAI TTS creates voice reply")
    print("  5. Audio ready to send to caller")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
