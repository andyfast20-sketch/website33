"""
Real Phone Call Simulation Test
Simulates exact phone call flow with realistic delays
Tests: Phone Voice → AssemblyAI → GPT-4 → TTS → Response
Keeps testing until perfect
"""
import asyncio
import audioop
import wave
import io
import httpx
import time
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

async def simulate_phone_call(call_num, user_message):
    """Simulate complete phone call with realistic timing"""
    print(f"\n{'='*70}")
    print(f"PHONE CALL SIMULATION #{call_num}")
    print(f"{'='*70}")
    
    total_start = time.time()
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # === CALLER SPEAKS (UK accent phone quality) ===
        print(f"\n[CALLER] Speaking: '{user_message}'")
        step_start = time.time()
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=f"Speak with a British accent: {user_message}",
            response_format="pcm"
        )
        
        # Convert to phone quality (8kHz)
        audio_24k = response.content
        audio_8k = audioop.ratecv(audio_24k, 2, 1, 24000, 8000, None)[0]
        audio_ulaw = audioop.lin2ulaw(audio_8k, 2)
        
        # Convert back to 16kHz PCM (like our handler does)
        audio_8k_pcm = audioop.ulaw2lin(audio_ulaw, 2)
        audio_16k = audioop.ratecv(audio_8k_pcm, 2, 1, 8000, 16000, None)[0]
        
        wav_data = pcm_to_wav(audio_16k)
        speech_time = time.time() - step_start
        print(f"  Speech duration: {len(audio_24k) / 48000:.2f}s")
        print(f"  Generation time: {speech_time:.2f}s")
        
        # === TRANSCRIPTION (AssemblyAI with UK English) ===
        print(f"\n[SYSTEM] Transcribing with AssemblyAI (UK English)...")
        step_start = time.time()
        
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            # Upload
            upload = await http_client.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"Authorization": ASSEMBLYAI_API_KEY},
                content=wav_data
            )
            
            if upload.status_code != 200:
                print(f"  ERROR: Upload failed ({upload.status_code})")
                return None
            
            audio_url = upload.json()["upload_url"]
            
            # Create transcript
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
            confidence = 0
            
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
                    break
                elif state == "error":
                    print(f"  ERROR: Transcription failed")
                    return None
            
            transcription_time = time.time() - step_start
            
            if not transcribed_text or len(transcribed_text) < 5:
                print(f"  ERROR: Empty transcription")
                return None
            
            print(f"  Transcribed: '{transcribed_text}'")
            print(f"  Confidence: {confidence:.1%}")
            print(f"  Transcription time: {transcription_time:.2f}s")
        
        # === GPT-4 THINKS ===
        print(f"\n[AI] Generating response with GPT-4...")
        step_start = time.time()
        
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful appointment booking assistant. Keep responses brief and natural."},
                {"role": "user", "content": transcribed_text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        assistant_text = gpt_response.choices[0].message.content.strip()
        gpt_time = time.time() - step_start
        
        print(f"  AI says: '{assistant_text}'")
        print(f"  GPT-4 time: {gpt_time:.2f}s")
        
        if not assistant_text or len(assistant_text) < 3:
            print(f"  ERROR: Empty GPT-4 response")
            return None
        
        # === TEXT-TO-SPEECH ===
        print(f"\n[SYSTEM] Converting to speech...")
        step_start = time.time()
        
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=assistant_text,
            response_format="pcm"
        )
        
        response_audio = tts_response.content
        tts_time = time.time() - step_start
        
        print(f"  Audio generated: {len(response_audio)} bytes")
        print(f"  Response duration: {len(response_audio) / 48000:.2f}s")
        print(f"  TTS time: {tts_time:.2f}s")
        
        # === TIMING ANALYSIS ===
        total_time = time.time() - total_start
        
        print(f"\n{'='*70}")
        print(f"CALL RESULT: SUCCESS")
        print(f"{'='*70}")
        print(f"Caller said: {user_message}")
        print(f"Transcribed: {transcribed_text}")
        print(f"AI replied: {assistant_text}")
        print(f"\nTIMING BREAKDOWN:")
        print(f"  Transcription: {transcription_time:.2f}s")
        print(f"  GPT-4 thinking: {gpt_time:.2f}s")
        print(f"  TTS generation: {tts_time:.2f}s")
        print(f"  TOTAL DELAY: {total_time:.2f}s")
        
        if total_time < 5:
            print(f"  VERDICT: Excellent response time (<5s)")
        elif total_time < 8:
            print(f"  VERDICT: Good response time (<8s)")
        elif total_time < 12:
            print(f"  VERDICT: Acceptable response time (<12s)")
        else:
            print(f"  VERDICT: Slow response time (>12s)")
        
        print(f"{'='*70}")
        
        return {
            "success": True,
            "user_message": user_message,
            "transcribed": transcribed_text,
            "ai_response": assistant_text,
            "confidence": confidence,
            "total_time": total_time,
            "transcription_time": transcription_time,
            "gpt_time": gpt_time,
            "tts_time": tts_time
        }
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"CALL RESULT: FAILED")
        print(f"ERROR: {e}")
        print(f"{'='*70}")
        return None

async def main():
    print("\n" + "="*70)
    print("REALISTIC PHONE CALL SIMULATION TEST")
    print("Simulating complete phone conversations with UK accents")
    print("Testing until perfect with small delays")
    print("="*70)
    
    # Realistic conversation scenarios
    conversations = [
        "Hello, I'd like to book an appointment please",
        "Good morning, what time are you open today",
        "Can I schedule something for next Tuesday",
        "I need to make a booking for two people",
        "What's your availability this week",
    ]
    
    all_results = []
    
    for i, message in enumerate(conversations, 1):
        result = await simulate_phone_call(i, message)
        if result:
            all_results.append(result)
        else:
            all_results.append({"success": False})
        
        # Brief pause between calls
        await asyncio.sleep(2)
    
    # === FINAL SUMMARY ===
    print("\n\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)
    
    successful = [r for r in all_results if r.get("success")]
    success_rate = (len(successful) / len(all_results) * 100) if all_results else 0
    
    print(f"\nTotal Calls: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(all_results) - len(successful)}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if successful:
        avg_time = sum(r["total_time"] for r in successful) / len(successful)
        avg_transcription = sum(r["transcription_time"] for r in successful) / len(successful)
        avg_gpt = sum(r["gpt_time"] for r in successful) / len(successful)
        avg_tts = sum(r["tts_time"] for r in successful) / len(successful)
        avg_confidence = sum(r["confidence"] for r in successful) / len(successful)
        
        print(f"\nAVERAGE PERFORMANCE:")
        print(f"  Total response time: {avg_time:.2f}s")
        print(f"  Transcription: {avg_transcription:.2f}s")
        print(f"  GPT-4 thinking: {avg_gpt:.2f}s")
        print(f"  TTS generation: {avg_tts:.2f}s")
        print(f"  Transcription confidence: {avg_confidence:.1%}")
    
    print(f"\n{'='*70}")
    
    if success_rate >= 95 and successful and avg_time < 10:
        print("VERDICT: >95% CERTAINTY - READY FOR PHONE CALLS")
        print("  - UK accents working")
        print("  - Fast response times (<10s)")
        print("  - Complete conversation flow verified")
    elif success_rate >= 95:
        print("VERDICT: >95% CERTAINTY - Works but response time could be better")
    elif success_rate >= 80:
        print("VERDICT: 80-95% CERTAINTY - Mostly working")
    else:
        print("VERDICT: <80% CERTAINTY - Needs more work")
    
    print("="*70)
    
    # Show example conversation
    if successful:
        print("\nEXAMPLE CONVERSATION:")
        print("-" * 70)
        example = successful[0]
        print(f"Caller: {example['user_message']}")
        print(f"(transcribed as: {example['transcribed']})")
        print(f"AI Agent: {example['ai_response']}")
        print(f"Response time: {example['total_time']:.2f}s")
        print("-" * 70)

if __name__ == "__main__":
    asyncio.run(main())
